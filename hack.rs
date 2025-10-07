//! Safe registration script (cleaned from "hack" code).
//! - No external posting of coldkey.
//! - Local signing only (sr25519).
//! - Uses dynamic tx via subxt.
//! - Proper storage decoding for u128 -> u64 conversion.
//! - Simpler loop with backoff, no tokio::spawn for submit.

use clap::Parser;
use env_logger;
use log::{error, info, warn};
use scale_value::{Value};
use serde::Deserialize;
use sp_core::H256;
use std::sync::Arc;
use std::time::Duration;
use subxt::dynamic::tx;
use subxt::blocks::ExtrinsicEvents;
use subxt::ext::sp_core::{sr25519, Pair};
use subxt::{tx::PairSigner, OnlineClient, SubstrateConfig};
use tokio::time::sleep;

/// CLI args
#[derive(Parser, Deserialize, Debug)]
#[clap(author, version, about, long_about = None)]
struct RegistrationParams {
    /// coldkey as a secret seed / mnemonic (kept local)
    #[clap(long)]
    coldkey: String,

    /// hotkey to register (string)
    #[clap(long)]
    hotkey: String,

    /// network UID
    #[clap(long)]
    netuid: u16,

    /// maximum allowed burn cost
    #[clap(long, default_value = "5000000000")]
    max_cost: u64,

    /// chain endpoint
    #[clap(long, default_value = "wss://entrypoint-finney.opentensor.ai:443")]
    chain_endpoint: String,

    /// delay between attempts in seconds
    #[clap(long, default_value = "6")]
    attempt_interval_secs: u64,

    /// optional maximum attempts (0 = infinite)
    #[clap(long, default_value = "0")]
    max_attempts: u64,
}

/// Human-friendly timestamp helper for logs.
fn now_ts() -> String {
    chrono::Utc::now().to_rfc3339()
}

/// Query the on-chain `SubtensorModule::Burn` storage for `netuid`.
/// Returns a `u128`-backed value converted to `u128`, then optionally cast to u64 by caller.
async fn get_recycle_cost(
    client: &OnlineClient<SubstrateConfig>,
    netuid: u16,
) -> Result<u128, Box<dyn std::error::Error>> {
    let latest_block = client.blocks().at_latest().await?;
    // The storage key expects a U128 primitive keyed by netuid
    let burn_key = subxt::storage::dynamic(
        "SubtensorModule",
        "Burn",
        vec![Value::primitive(scale_value::Primitive::U128(netuid as u128))],
    );

    let opt_val = client
        .storage()
        .at(latest_block.hash())
        .fetch(&burn_key)
        .await?;

    let value = opt_val.ok_or_else(|| format!("Burn value not found for netuid {}", netuid))?;
    // Decode as u128 (common for balances)
    let burn_u128 = value.as_type::<u128>()?;
    Ok(burn_u128)
}

/// Attempts to sign & submit a single `SubtensorModule::burned_register(netuid, hotkey)`
/// using the provided signer. Returns the events on success.
async fn sign_and_submit_register(
    client: &OnlineClient<SubstrateConfig>,
    signer: &PairSigner<SubstrateConfig, sr25519::Pair>,
    netuid: u16,
    hotkey_pub: Vec<u8>,
) -> Result<ExtrinsicEvents<SubstrateConfig>, Box<dyn std::error::Error>> {
    // Build a dynamic tx: burned_register(netuid: u16, hotkey: <AccountId as bytes>)
    let call = tx(
        "SubtensorModule",
        "burned_register",
        vec![
            Value::from(netuid as u16),
            Value::from_bytes(hotkey_pub),
        ],
    );

    // Sign, submit, and watch for finalized success
    let progress = client
        .tx()
        .sign_and_submit_then_watch(&call, signer, Default::default())
        .await?;

    let events = progress.wait_for_finalized_success().await?;
    Ok(events)
}

/// Core registration loop:
/// - connect to chain
/// - prepare local signer from `coldkey`
/// - on each finalized block or on interval: check cost, submit register when allowed
async fn register_hotkey(params: &RegistrationParams) -> Result<(), Box<dyn std::error::Error>> {
    info!("{} | connecting to {}", now_ts(), params.chain_endpoint);
    let client = OnlineClient::<SubstrateConfig>::from_url(&params.chain_endpoint).await?;
    let client = Arc::new(client);

    // Parse keys locally (panic/return error if invalid)
    let cold_pair = sr25519::Pair::from_string(&params.coldkey, None)
        .map_err(|e| format!("Invalid coldkey: {:?}", e))?;
    let hot_pair = sr25519::Pair::from_string(&params.hotkey, None)
        .map_err(|e| format!("Invalid hotkey: {:?}", e))?;

    let signer = PairSigner::new(cold_pair);
    let signer = Arc::new(signer);

    let hot_pub = hot_pair.public().0.to_vec();

    info!(
        "{} | prepared signer (hotkey pub = 0x{})",
        now_ts(),
        hex::encode(&hot_pub)
    );

    // Simple attempt loop with delay and optional attempt limit
    let mut attempts: u64 = 0;
    loop {
        attempts = attempts.saturating_add(1);

        if params.max_attempts > 0 && attempts > params.max_attempts {
            warn!("{} | reached max attempts ({}). Exiting.", now_ts(), params.max_attempts);
            return Err("max attempts reached".into());
        }

        info!("{} | attempt #{}", now_ts(), attempts);

        // Query recycle cost (u128) and compare to allowed max_cost (u64)
        match get_recycle_cost(&client, params.netuid).await {
            Ok(burn_u128) => {
                // Convert to u128 -> compare
                let allowed = params.max_cost as u128;
                info!("{} | chain burn cost = {} (allowed <= {})", now_ts(), burn_u128, allowed);
                if burn_u128 > allowed {
                    warn!("{} | burn cost {} > allowed {}; sleeping then retrying", now_ts(), burn_u128, allowed);
                    sleep(Duration::from_secs(params.attempt_interval_secs)).await;
                    continue;
                }
            }
            Err(e) => {
                warn!("{} | could not read burn cost: {:?}; will retry", now_ts(), e);
                sleep(Duration::from_secs(params.attempt_interval_secs)).await;
                continue;
            }
        }

        // Sign + submit directly (no spawn). On success, log events and return Ok.
        match sign_and_submit_register(&client, &*signer, params.netuid, hot_pub.clone()).await {
            Ok(events) => {
                let block_hash: H256 = events.extrinsic_hash();
                info!("{} | Registration succeeded. Extrinsic hash: {:?}", now_ts(), block_hash);
                // Optionally inspect events for relevant SubtensorModule::Registered or similar
                for ev in events.iter().filter_map(Result::ok) {
                    info!("{} | event: {}::{}", now_ts(), ev.pallet_name(), ev.variant_name());
                }
                return Ok(());
            }
            Err(e) => {
                error!("{} | submit failed: {:?}; retrying after delay", now_ts(), e);
                // small backoff before next attempt
                sleep(Duration::from_secs(params.attempt_interval_secs)).await;
                continue;
            }
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // initialize logger
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    let params = RegistrationParams::parse();

    info!("{} | starting registration (netuid {})", now_ts(), params.netuid);

    if let Err(e) = register_hotkey(&params).await {
        error!("{} | registration failed: {:?}", now_ts(), e);
        return Err(e);
    }

    info!("{} | registration process finished", now_ts());
    Ok(())
}
