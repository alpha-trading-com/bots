from typing import Dict, List
from asyncio.log import logger
import time
import bittensor as bt
import numpy as np
from config import *
import logging
from datetime import datetime
import os

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Create a log filename with timestamp
log_filename = f"logs/app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # File handler - writes to file
        logging.FileHandler(log_filename),
        # Stream handler - writes to console
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def old_register(
    netuid, subtensor, wallet, wait_for_inclusion=True, wait_for_finalization=False
):
    while True:
        try:
            receipt = subtensor._do_burned_register(
                netuid=netuid,
                wallet=wallet,
                wait_for_inclusion=wait_for_inclusion,
                wait_for_finalization=wait_for_finalization,
            )
            print(receipt)
            if receipt[0] == True:
                print(
                    f"Successfully registered wallet {wallet.name} {wallet.hotkey} to subnet {netuid}"
                )
                break
            elif "HotKeyAlreadyRegisteredInSubNet" in receipt[1]:
                print(f"Hotkey {wallet.hotkey} already registered in subnet {netuid}")
                break
        except Exception as e:
            print(e)
            continue

def dtao_register(netuid, subtensor, wallet):
    while True:
        try:
            receipt = subtensor.burned_register(
                netuid=netuid,
                wallet=wallet,
            )
            print(receipt)
            if receipt[0] == True:
                print(f"Successfully registered wallet {wallet.name} {wallet.hotkey} to subnet {netuid}")
                break
            elif "HotKeyAlreadyRegisteredInSubNet" in receipt[1]:
                print(f"Hotkey {wallet.hotkey} already registered in subnet {netuid}")
                break
        except Exception as e:
            print(e)
            continue

def exchange_rates(netuid, subtensor):
    subnet = subtensor.subnet(netuid=netuid)
    # print("alpha_to_tao_with_slippage", subnet.alpha_to_tao_with_slippage(1))
    # print(
    #     "alpha_to_tao_with_slippage percentage",
    #     subnet.alpha_to_tao_with_slippage(1, percentage=True),
    # )

    # print("tao_to_alpha_with_slippage", subnet.tao_to_alpha_with_slippage(1))
    # print(
    #     "tao_to_alpha_with_slippage percentage",
    #     subnet.tao_to_alpha_with_slippage(1, percentage=True),
    # )

    # print("tao_to_alpha", subnet.tao_to_alpha(1))
    # print("alpha_to_tao", subnet.alpha_to_tao(1))
    
    return subnet.alpha_to_tao(1)

def watching_price(netuid, subtensor):
  while True:
    try:
      logger.info(f"Netuid: {netuid} ===> price: {exchange_rates(netuid, subtensor)}")
      subtensor.wait_for_block()
    except Exception as e:
      logger.error(f"Error in watching_price: {e}")
      continue

def get_balance_coldkey(subtensor, address):
    balance = subtensor.get_balance(address)
    logger.info(f"==== Balance of {address}: {balance} ====")
    return balance

def stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount):
    try:
        subnet = subtensor.subnet(netuid=netuid)
        amount = bt.Balance.from_tao(tao_amount)
        
        stake = subtensor.add_stake(
            netuid=netuid,
            amount=amount,
            wallet=wallet,
            hotkey_ss58=hotkey
        )
        
        current_stake = subtensor.get_stake(
            coldkey_ss58 = wallet.coldkeypub.ss58_address,
            hotkey_ss58 = hotkey,
            netuid = netuid,
        )
        logger.info(f'=== staked netuid {netuid} price {subnet.price} stake {current_stake} ===')
        logger.info(f"=== staked {amount} TAO to {hotkey} on {netuid} ===\n")
        return True
    except Exception as e:
        logger.error(f"Error during staking: {e}")
        return False

def calc_tao_amount(netuid, subtensor, wallet, hotkey):
    subnet = subtensor.subnet(netuid=netuid)
    return subnet.price

def unstake_from_subnet(netuid, subtensor, wallet, hotkey, tao_amount=None):
    try:
        subnet = subtensor.subnet(netuid=netuid)
        
        if tao_amount is not None:
            amount = subnet.tao_to_alpha(tao_amount)
            result = subtensor.unstake(
                netuid=netuid,
                amount=amount,
                wallet=wallet,
                hotkey_ss58=hotkey
            )
            logger.info(f"==== Unstaked {amount} TAO from {hotkey} on {netuid} || result: {result} ====")
        else:
            # Unstake all if no amount specified
            result = subtensor.unstake(
                wallet=wallet,
                hotkey_ss58=hotkey,
                netuid=netuid
            )
            logger.info(f"==== Unstaked all TAO from {hotkey} on {netuid} || result: {result} ====")
        return result
    except Exception as e:
        logger.error(f"Error during unstaking: {e}")
        return False

async def get_stake(subtensor: bt.AsyncSubtensor, coldkey: str, hotkey: str, netuid: int) -> bt.Balance:
    try:
        stake = await subtensor.get_stake(coldkey_ss58=coldkey, hotkey_ss58=hotkey, netuid=netuid)
        if DEBUG_MODE:
            logger.info(f"[Net {netuid}] Current stake: {stake.tao:.5f} TAO")
        return stake
    except Exception as e:
        logger.error(f"Failed to get stake for {hotkey} on net {netuid}: {e}")
        return bt.Balance(0)


async def get_balance(subtensor: bt.AsyncSubtensor, address: str) -> bt.Balance:
    try:
        balance = await subtensor.get_balance(address)
        if DEBUG_MODE:
            logger.info(f"Balance: {balance.tao:.5f} TAO")
        return balance
    except Exception as e:
        logger.error(f"Failed to get balance for {address}: {e}")
        return bt.Balance(0)

async def get_subnet_neurons(subtensor: bt.AsyncSubtensor, netuid: int) -> List[Dict]:
    try:
        neurons = await subtensor.get_neurons(netuid=netuid)
        return neurons
    except Exception as e:
        logger.error(f"Failed to get neurons for subnet {netuid}: {e}")
        return []
    
async def get_subnet_info(subtensor: bt.AsyncSubtensor, netuid: int) -> dict:
    try:
        # Get subnet properties
        subnet_info = await subtensor.get_subnet_info(netuid=netuid)
        return subnet_info
    except Exception as e:
        logger.error(f"Failed to get subnet info for {netuid}: {e}")
        return {}
    
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate Relative Strength Index for given price data."""
    if len(prices) < period + 1:
        return 50  # Not enough data, return neutral value
    
    deltas = np.diff(prices)
    gains = np.array([max(0, d) for d in deltas])
    losses = np.array([max(0, -d) for d in deltas])
    
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    if avg_loss == 0:
        return 100  # No losses, RSI is 100
    
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def detect_price_trend(prices: List[float]) -> str:
    """Analyze price trends and return a trend label."""
    if len(prices) < PRICE_WINDOW_LONG:
        return "neutral"  # Not enough data
    
    # Calculate short and long moving averages
    short_ma = np.mean(prices[-PRICE_WINDOW_SHORT:])
    long_ma = np.mean(prices[-PRICE_WINDOW_LONG:])
    
    # Calculate RSI
    rsi = calculate_rsi(prices, RSI_PERIOD)
    
    # Calculate volatility as standard deviation of percentage changes
    pct_changes = [100 * (prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
    volatility = np.std(pct_changes[-PRICE_WINDOW_SHORT:])
    
    # Check recent drop or gain
    recent_change = (prices[-1] / prices[-5] - 1) * 100  # 5-period % change
    
    # Decision logic
    if rsi < RSI_OVERSOLD and short_ma < long_ma and recent_change < -PRICE_DIP_THRESHOLD:
        return "strong_buy"
    elif rsi < 40 and short_ma < long_ma:
        return "buy"
    elif rsi > RSI_OVERBOUGHT and short_ma > long_ma:
        return "strong_sell"
    elif rsi > 60 and short_ma > long_ma:
        return "sell"
    elif volatility > VOLATILITY_THRESHOLD:
        return "volatile"
    else:
        return "neutral"
    
