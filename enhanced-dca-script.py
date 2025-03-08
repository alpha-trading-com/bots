import asyncio
import bittensor as bt
from retry import retry
import time
import logging
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, Tuple, List, Optional, Any
from rich.console import Console, Group
from rich.table import Table
from rich.columns import Columns
from rich.live import Live
from rich.panel import Panel
from rich.style import Style
from rich import box
import os
import json
from pathlib import Path
import aiohttp
import numpy as np
import pandas as pd
from scipy import stats
import statistics


# Configuration
SUBNET_CONFIGS: Dict[int, Tuple[float, str]] = {
    64: (0.005, "5CsvRJXuR955WojnGMdok1hbhffZyB4N5ocrv82f3p5A2zVp"),
    4: (0.005, "5CsvRJXuR955WojnGMdok1hbhffZyB4N5ocrv82f3p5A2zVp"),
    42: (0.005, "5D4gEn5S422dTGR5NJJKZ93FNV6hDmfwDPfxFNgcoVnUkZ4f"),
    8: (0.005, "5HYk8DMKWK8TJyPzZJ9vmZk7B5NPCgjnZoyZ1ZsB54RXdN47"),
    34: (0.005, "5CsvRJXuR955WojnGMdok1hbhffZyB4N5ocrv82f3p5A2zVp"),
    19: (0.005, "5GP7c3fFazW9GXK8Up3qgu2DJBk8inu4aK9TZy3RuoSWVCMi"),
    13: (0.005, "5HYk8DMKWK8TJyPzZJ9vmZk7B5NPCgjnZoyZ1ZsB54RXdN47"),
    51: (0.005, "5GP7c3fFazW9GXK8Up3qgu2DJBk8inu4aK9TZy3RuoSWVCMi"),
}

ROOT_NETUID = 0
ROOT_HOTKEY = "5CsvRJXuR955WojnGMdok1hbhffZyB4N5ocrv82f3p5A2zVp"

# Advanced settings
INTERVAL_MINUTES = 60  # Default interval for checking - will be adjusted dynamically
DIVIDEND_CHECK_INTERVAL = timedelta(seconds=30)
PRICE_CHECK_INTERVAL = timedelta(minutes=5)
VALIDATOR_TRACK_INTERVAL = timedelta(minutes=15)
APY_CHECK_INTERVAL = timedelta(hours=4)

# Thresholds
MIN_ROOT_STAKE = 0.1
MIN_STAKE_THRESHOLD = 0.005
VOLATILITY_THRESHOLD = 0.15  # 15% threshold for high volatility
PRICE_DIP_THRESHOLD = 0.05  # 5% price drop considered a dip
VALIDATOR_ACTIVITY_THRESHOLD = 3  # Number of major validators needed to trigger front-running
APY_ROTATION_THRESHOLD = 0.2  # 20% APY difference to trigger rotation
SUBNET_SATURATION_THRESHOLD = 0.85  # 85% saturation threshold

# APY tracking
TOP_APY_SUBNETS = 3  # Number of top APY subnets to rotate between

# Price trend settings
PRICE_WINDOW_SHORT = 12  # 1 hour if checking every 5 minutes
PRICE_WINDOW_LONG = 72   # 6 hours if checking every 5 minutes
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

AUTO_MODE = True
DEBUG_MODE = True  # Set to True for more detailed output
ENABLE_NOTIFICATIONS = True

# File paths
DATA_DIR = Path("data")
SCHEDULE_FILE = DATA_DIR / "staking_schedule-data.json"
PRICE_HISTORY_FILE = DATA_DIR / "price_history.json"
APY_HISTORY_FILE = DATA_DIR / "apy_history.json"
VALIDATOR_ACTIVITY_FILE = DATA_DIR / "validator_activity.json"
SUBNET_STATS_FILE = DATA_DIR / "subnet_stats.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    filename='enhanced_staking_operations.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

console = Console()
header_style = Style(color="bright_cyan", bold=True)
value_style = Style(color="white", bold=True)
alert_style = Style(color="bright_red", bold=True)
success_style = Style(color="bright_green", bold=True)

wallet = bt.wallet(name="sec_ck2")
wallet.unlock_coldkey()

# History logs for different components
history_log: List[str] = []
price_alerts: List[str] = []
validator_alerts: List[str] = []
apy_alerts: List[str] = []

# In-memory data stores
price_data = []
validator_activities = {}
subnet_apy_data = {}
subnet_saturation = {}
strategy_metrics = {
    "dca_triggers": 0,
    "volatility_adjustments": 0,
    "frontrun_actions": 0,
    "apy_rotations": 0,
    "saturation_avoidance": 0,
    "successful_stakes": 0,
    "failed_stakes": 0
}


# ================== Data Management Functions ==================

def read_json_file(file_path: Path, default_value: Any) -> Any:
    if not file_path.exists():
        with open(file_path, 'w') as f:
            json.dump(default_value, f)
        logger.info(f"Created {file_path.name} with default values")
        return default_value

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return default_value


def write_json_file(file_path: Path, data: Any) -> None:
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error writing to {file_path}: {e}")


def read_schedule() -> dict:
    default_schedule = {
        "next_staking": "1999-01-01T00:00:00",
        "interval_minutes": INTERVAL_MINUTES,
        "dynamic_interval": True
    }
    
    data = read_json_file(SCHEDULE_FILE, default_schedule)
    
    return {
        "next_staking": datetime.fromisoformat(data["next_staking"]) if data["next_staking"] else None,
        "interval_minutes": data.get("interval_minutes", INTERVAL_MINUTES),
        "dynamic_interval": data.get("dynamic_interval", True)
    }


def write_schedule(next_staking: datetime, interval_minutes: int, dynamic_interval: bool = True) -> None:
    data = {
        "next_staking": next_staking.isoformat(),
        "interval_minutes": interval_minutes,
        "dynamic_interval": dynamic_interval
    }
    write_json_file(SCHEDULE_FILE, data)


def read_price_history() -> List[Dict[str, Any]]:
    return read_json_file(PRICE_HISTORY_FILE, [])


def write_price_history(data: List[Dict[str, Any]]) -> None:
    write_json_file(PRICE_HISTORY_FILE, data)


def read_apy_history() -> Dict[int, List[Dict[str, Any]]]:
    return read_json_file(APY_HISTORY_FILE, {})


def write_apy_history(data: Dict[int, List[Dict[str, Any]]]) -> None:
    write_json_file(APY_HISTORY_FILE, data)


def read_validator_activity() -> Dict[str, List[Dict[str, Any]]]:
    return read_json_file(VALIDATOR_ACTIVITY_FILE, {})


def write_validator_activity(data: Dict[str, List[Dict[str, Any]]]) -> None:
    write_json_file(VALIDATOR_ACTIVITY_FILE, data)


def read_subnet_stats() -> Dict[int, Dict[str, Any]]:
    return read_json_file(SUBNET_STATS_FILE, {})


def write_subnet_stats(data: Dict[int, Dict[str, Any]]) -> None:
    write_json_file(SUBNET_STATS_FILE, data)


def next_staking_time(reference_time: datetime = None, interval_minutes: int = INTERVAL_MINUTES) -> datetime:
    if interval_minutes <= 0:
        raise ValueError("Interval must be greater than 0 minutes")

    ref_time = reference_time or datetime.utcnow()
    minutes_since_midnight = ref_time.hour * 60 + ref_time.minute
    next_interval = ((minutes_since_midnight // interval_minutes) + 1) * interval_minutes

    if next_interval >= 24 * 60:
        next_day = ref_time.date() + timedelta(days=1)
        return datetime.combine(next_day, dt_time(0, 0)).replace(tzinfo=ref_time.tzinfo)

    next_hours = next_interval // 60
    next_minutes = next_interval % 60

    return datetime.combine(
        ref_time.date(),
        dt_time(next_hours, next_minutes)
    ).replace(tzinfo=ref_time.tzinfo)


def append_history(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    history_log.append(entry)
    if len(history_log) > 20:
        del history_log[0]
    logger.info(f"History: {message}")


def append_price_alert(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    price_alerts.append(entry)
    if len(price_alerts) > 10:
        del price_alerts[0]
    logger.info(f"Price Alert: {message}")


def append_validator_alert(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    validator_alerts.append(entry)
    if len(validator_alerts) > 10:
        del validator_alerts[0]
    logger.info(f"Validator Alert: {message}")


def append_apy_alert(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    apy_alerts.append(entry)
    if len(apy_alerts) > 10:
        del apy_alerts[0]
    logger.info(f"APY Alert: {message}")


def user_confirmation(prompt: str) -> bool:
    if AUTO_MODE:
        return True
    return console.input(prompt + " (y/n): ").strip().lower() == 'y'


# ================== Blockchain Interface Functions ==================

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


@retry(Exception, tries=3, delay=2, backoff=2, max_delay=30)
async def unstake_excess(subtensor: bt.AsyncSubtensor, wallet: bt.wallet, netuid: int, hotkey: str, amount: float) -> float:
    coldkey = wallet.coldkeypub.ss58_address
    try:
        initial = await get_stake(subtensor, coldkey, hotkey, netuid)
        max_safe_unstake = max(0, initial.tao - MIN_ROOT_STAKE)
        actual_unstake = min(amount, max_safe_unstake)

        if actual_unstake <= 0:
            logger.warning(f"[Net {netuid}] Unsafe unstake attempt: {amount:.5f} TAO requested, but only {max_safe_unstake:.5f} TAO available.")
            append_history(f"Unstake blocked on Net {netuid} (would breach minimum)")
            return 0

        logger.info(f"[Net {netuid}] Request to unstake {actual_unstake:.5f} TAO (Safe limit: {max_safe_unstake:.5f} TAO)")

        if not user_confirmation(f"Unstake {actual_unstake:.5f} TAO on network {netuid}?"):
            logger.info("Unstake cancelled by user")
            append_history(f"Cancelled unstaking on Net {netuid}")
            return 0

        await subtensor.unstake(
            wallet=wallet,
            netuid=netuid,
            hotkey_ss58=hotkey,
            amount=bt.Balance.from_tao(actual_unstake)
        )
        await asyncio.sleep(3)
        new_stake = await get_stake(subtensor, coldkey, hotkey, netuid)

        if new_stake.tao < MIN_ROOT_STAKE:
            deficit = MIN_ROOT_STAKE - new_stake.tao
            logger.warning(f"[Net {netuid}] EMERGENCY RESTAKE NEEDED: {deficit:.5f} TAO")
            restake_result = await stake_dividend(subtensor, wallet, netuid, hotkey, deficit)
            if restake_result > 0:
                append_history(f"Emergency restake: {deficit:.5f} TAO on Net {netuid}")
            else:
                append_history(f"Emergency restake FAILED on Net {netuid}")
            new_stake = await get_stake(subtensor, coldkey, hotkey, netuid)

        logger.info(f"[Net {netuid}] Unstaked. Final stake: {new_stake.tao:.5f} TAO")
        append_history(f"Unstaked {actual_unstake:.5f} TAO on Net {netuid}")
        return actual_unstake
    except Exception as e:
        logger.error(f"Unstaking failed on Net {netuid}: {e}")
        append_history(f"Unstaking failed on Net {netuid}: {e}")
        return 0
    finally:
        await asyncio.sleep(15)


@retry(Exception, tries=3, delay=2, backoff=2, max_delay=30)
async def stake_dividend(subtensor: bt.AsyncSubtensor, wallet: bt.wallet, netuid: int, hotkey: str, amount: float) -> float:
    coldkey = wallet.coldkeypub.ss58_address
    try:
        initial = await get_stake(subtensor, coldkey, hotkey, netuid)
        logger.info(f"[Net {netuid}] Request to stake {amount:.5f} TAO (Current stake: {initial.tao:.5f} TAO)")
        
        if not user_confirmation(f"Stake {amount:.5f} TAO on network {netuid}?"):
            logger.info("Staking cancelled by user")
            append_history(f"Cancelled staking on Net {netuid}")
            return 0

        await subtensor.add_stake(
            wallet=wallet,
            netuid=netuid,
            hotkey_ss58=hotkey,
            amount=bt.Balance.from_tao(amount)
        )
        await asyncio.sleep(3)
        new_stake = await get_stake(subtensor, coldkey, hotkey, netuid)

        logger.info(f"[Net {netuid}] Staked. New stake: {new_stake.tao:.5f} TAO (was {initial.tao:.5f} TAO)")
        append_history(f"Staked {amount:.5f} TAO on Net {netuid}")
        strategy_metrics["successful_stakes"] += 1
        return amount
    except Exception as e:
        logger.error(f"Staking failed on Net {netuid}: {e}")
        append_history(f"Staking failed on Net {netuid}: {e}")
        strategy_metrics["failed_stakes"] += 1
        return 0
    finally:
        await asyncio.sleep(15)


async def process_subnet(subtensor: bt.AsyncSubtensor, wallet: bt.wallet, netuid: int, amount: float, hotkey: str) -> float:
    try:
        start = time.monotonic()
        staked = await stake_dividend(subtensor, wallet, netuid, hotkey, amount)
        duration = time.monotonic() - start
        logger.info(f"Staked {amount:.5f} TAO on Net {netuid} in {duration:.2f}s")
        return staked
    except Exception as e:
        logger.error(f"Staking error on Net {netuid}: {str(e)}")
        append_history(f"Staking error on Net {netuid}: {e}")
        return 0


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


# ================== Advanced Analytics Functions ==================

async def fetch_tao_price() -> Optional[float]:
    """Fetch TAO price from an API endpoint."""
    try:
        # This is a placeholder - replace with actual API endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.example.com/v1/tao/price") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("price", None)
    except Exception as e:
        logger.error(f"Failed to fetch TAO price: {e}")
    
    # For demo purposes, generate a mock price around $40 with some variance
    # Remove this in production and use real API data
    base_price = 40.0
    variance = base_price * 0.05  # 5% variance
    mock_price = base_price + (np.random.random() - 0.5) * 2 * variance
    return mock_price


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


def calculate_dynamic_dca_amount(trend: str, base_amount: float) -> float:
    """Calculate the dynamic DCA amount based on price trends."""
    multipliers = {
        "strong_buy": 2.0,
        "buy": 1.5,
        "neutral": 1.0,
        "sell": 0.7,
        "strong_sell": 0.5,
        "volatile": 0.8
    }
    
    multiplier = multipliers.get(trend, 1.0)
    return base_amount * multiplier


async def analyze_validator_movements(subtensor: bt.AsyncSubtensor) -> Dict[int, bool]:
    """Analyze validator movements to detect front-running opportunities."""
    frontrun_opportunities = {}
    try:
        # Read historical validator activity
        validator_history = read_validator_activity()
        current_time = datetime.utcnow()
        
        # Get current stakes for major validators across subnets
        for netuid in SUBNET_CONFIGS.keys():
            subnet_neurons = await get_subnet_neurons(subtensor, netuid)
            current_validators = {}
            
            # Identify top validators by stake
            for neuron in subnet_neurons:
                if hasattr(neuron, "stake") and hasattr(neuron, "hotkey"):
                    current_validators[neuron.hotkey] = float(neuron.stake)
            
            # Sort by stake descending
            top_validators = dict(sorted(current_validators.items(), key=lambda x: x[1], reverse=True)[:10])
            
            # Check for recent increases
            validator_increases = 0
            for hotkey, stake in top_validators.items():
                if hotkey not in validator_history:
                    validator_history[hotkey] = []
                
                # Add current observation
                validator_history[hotkey].append({
                    "timestamp": current_time.isoformat(),
                    "netuid": netuid,
                    "stake": stake
                })
                
                # Keep only recent history (last 2 days)
                validator_history[hotkey] = [
                    entry for entry in validator_history[hotkey] 
                    if datetime.fromisoformat(entry["timestamp"]) > current_time - timedelta(days=2)
                ]
                
                # Check if this validator has recently increased stake in this subnet
                same_subnet_history = [
                    entry for entry in validator_history[hotkey] 
                    if entry["netuid"] == netuid and
                    datetime.fromisoformat(entry["timestamp"]) > current_time - timedelta(hours=12)
                ]
                
                if len(same_subnet_history) > 1:
                    # Calculate recent growth rate
                    oldest = same_subnet_history[0]["stake"]
                    newest = same_subnet_history[-1]["stake"]
                    
                    if newest > oldest * 1.05:  # 5% growth threshold
                        validator_increases += 1
                        logger.info(f"Validator {hotkey[:10]}... increased stake in subnet {netuid}")
            
            # Mark subnet as opportunity if enough validators are increasing stakes
            frontrun_opportunities[netuid] = validator_increases >= VALIDATOR_ACTIVITY_THRESHOLD
            
            if frontrun_opportunities[netuid]:
                message = f"Front-run opportunity: {validator_increases} validators increasing on subnet {netuid}"
                append_validator_alert(message)
                logger.info(message)
        
        # Save updated validator history
        write_validator_activity(validator_history)
        
    except Exception as e:
        logger.error(f"Error analyzing validator movements: {e}")
    
    return frontrun_opportunities


async def calculate_subnet_apys(subtensor: bt.AsyncSubtensor) -> Dict[int, float]:
    """Calculate and track APYs for each subnet."""
    subnet_apys = {}
    try:
        # Read historical APY data
        apy_history = read_apy_history()
        current_time = datetime.utcnow()
        
        for netuid in SUBNET_CONFIGS.keys():
            # Initialize if needed
            if str(netuid) not in apy_history:
                apy_history[str(netuid)] = []
            
            subnet_info = await get_subnet_info(subtensor, netuid)
            
            # Extract emission data and calculate APY
            if subnet_info and hasattr(subnet_info, "emission_value"):
                emission = float(subnet_info.emission_value)
                
                # Calculate total stake in subnet
                neurons = await get_subnet_neurons(subtensor, netuid)
                total_stake = sum(float(neuron.stake) for neuron in neurons if hasattr(neuron, "stake"))
                
                if total_stake > 0:
                    # Simple APY calculation (annualized)
                    apy = (emission / total_stake) * 365 * 100
                    subnet_apys[netuid] = apy
                    
                    # Add to history
                    apy_history[str(netuid)].append({
                        "timestamp": current_time.isoformat(),
                        "apy": apy,
                        "total_stake": total_stake,
                        "emission": emission
                    })
                    
                    # Keep only recent history (last month)
                    apy_history[str(netuid)] = [
                        entry for entry in apy_history[str(netuid)]
                        if datetime.fromisoformat(entry["timestamp"]) > current_time - timedelta(days=30)
                    ]
                    
                    # Calculate saturation metrics
                    saturation_info = {}
                    if hasattr(subnet_info, "max_stake") and float(subnet_info.max_stake) > 0:
                        max_stake = float(subnet_info.max_stake)
                        saturation_ratio = total_stake / max_stake
                        saturation_info = {
                            "ratio": saturation_ratio,
                            "is_saturated": saturation_ratio > SUBNET_SATURATION_THRESHOLD
                        }
                    
                    subnet_saturation[netuid] = saturation_info
                    
                    # Log APY information
                    logger.info(f"Subnet {netuid} APY: {apy:.2f}%, Total Stake: {total_stake:.2f} TAO")
                    
                    if saturation_info.get("is_saturated", False):
                        message = f"Subnet {netuid} is saturated ({saturation_ratio:.1%})"
                        append_apy_alert(message)
        
        # Save updated APY history
        write_apy_history(apy_history)
        
    except Exception as e:
        logger.error(f"Error calculating subnet APYs: {e}")
    
    return subnet_apys


async def get_top_apy_subnets(subnet_apys: Dict[int, float], excluding_saturated: bool = True) -> List[int]:
    """Get the top APY subnets, optionally excluding saturated ones."""
    filtered_apys = {}
    
    for netuid, apy in subnet_apys.items():
        # Skip saturated subnets if requested
        if excluding_saturated and subnet_saturation.get(netuid, {}).get("is_saturated", False):
            continue
        filtered_apys[netuid] = apy
    
    # Sort by APY (descending) and return top N
    sorted_subnets = sorted(filtered_apys.items(), key=lambda x: x[1], reverse=True)
    top_subnets = [netuid for netuid, _ in sorted_subnets[:TOP_APY_SUBNETS]]
    
    return top_subnets


# ================== Advanced Strategy Functions ==================

async def determine_optimal_staking_time(price_history: List[Dict[str, Any]]) -> bool:
    """Determine if now is an optimal time to stake based on price analysis."""
    if not price_history or len(price_history) < 10:
        return True  # Not enough data, default to yes
    
    # Extract prices
    prices = [entry["price"] for entry in price_history]
    
    # Get latest price and trend
    current_price = prices[-1]
    trend = detect_price_trend(prices)
    
    # Calculate a simple z-score to see if price is unusually low
    if len(prices) > 30:
        mean_price = statistics.mean(prices[-30:])
        stdev_price = statistics.stdev(prices[-30:])
        z_score = (current_price - mean_price) / stdev_price if stdev_price > 0 else 0
        
        # If price is significantly below average (-1 standard deviation) or trending up from a bottom
        if z_score < -1.0 or trend in ["buy", "strong_buy"]:
            logger.info(f"Optimal staking time identified: price below average (z-score: {z_score:.2f})")
            return True
    
    # Check if we're in a strong buy zone
    if trend == "strong_buy":
        logger.info("Optimal staking time identified: strong buy signal")
        return True
    
    # Check if we're in a sell zone
    if trend in ["sell", "strong_sell"]:
        logger.info("Not an optimal staking time: sell signal active")
        return False
    
    # Default to normal DCA behavior
    return True


async def should_adjust_for_volatility(price_history: List[Dict[str, Any]]) -> Tuple[bool, float]:
    """Determine if we should adjust staking for volatility and by how much."""
    if not price_history or len(price_history) < PRICE_WINDOW_SHORT:
        return False, 1.0  # Not enough data, no adjustment
    
    # Extract prices
    prices = [entry["price"] for entry in price_history]
    
    # Calculate volatility metrics
    pct_changes = [100 * (prices[i] / prices[i-1] - 1) for i in range(1, len(prices))]
    recent_volatility = np.std(pct_changes[-PRICE_WINDOW_SHORT:])
    
    # Calculate RSI
    rsi = calculate_rsi(prices, RSI_PERIOD)
    
    # Check for volatility conditions
    if recent_volatility > VOLATILITY_THRESHOLD:
        # If market is volatile and RSI indicates oversold, increase stake
        if rsi < RSI_OVERSOLD:
            logger.info(f"High volatility with oversold conditions (RSI: {rsi:.1f}). Increasing stake.")
            strategy_metrics["volatility_adjustments"] += 1
            return True, 1.5  # Increase by 50%
        
        # If market is volatile and RSI indicates overbought, decrease stake
        elif rsi > RSI_OVERBOUGHT:
            logger.info(f"High volatility with overbought conditions (RSI: {rsi:.1f}). Decreasing stake.")
            strategy_metrics["volatility_adjustments"] += 1
            return True, 0.7  # Decrease by 30%
        
        # Just high volatility, slightly reduce stake
        else:
            logger.info(f"High volatility detected ({recent_volatility:.2f}). Slightly reducing stake.")
            strategy_metrics["volatility_adjustments"] += 1
            return True, 0.85  # Decrease by 15%
    
    return False, 1.0  # No adjustment


async def determine_best_subnets(subtensor: bt.AsyncSubtensor) -> List[Tuple[int, float]]:
    """Determine the best subnets to stake on based on APY, saturation, and validator activity."""
    try:
        # Calculate APYs
        subnet_apys = await calculate_subnet_apys(subtensor)
        
        # Check validator movements
        frontrun_opportunities = await analyze_validator_movements(subtensor)
        
        # Score each subnet
        subnet_scores = {}
        for netuid in SUBNET_CONFIGS.keys():
            base_score = subnet_apys.get(netuid, 0)
            
            # Penalize saturated subnets
            if subnet_saturation.get(netuid, {}).get("is_saturated", False):
                base_score *= 0.5
                strategy_metrics["saturation_avoidance"] += 1
            
            # Bonus for front-running opportunities
            if frontrun_opportunities.get(netuid, False):
                base_score *= 1.5
                strategy_metrics["frontrun_actions"] += 1
            
            subnet_scores[netuid] = base_score
        
        # Sort by score (descending)
        sorted_subnets = sorted(subnet_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Log top subnets
        for netuid, score in sorted_subnets[:3]:
            logger.info(f"Top subnet {netuid}: score {score:.2f} (APY: {subnet_apys.get(netuid, 0):.2f}%)")
        
        return sorted_subnets
    
    except Exception as e:
        logger.error(f"Error determining best subnets: {e}")
        return [(netuid, 1.0) for netuid in SUBNET_CONFIGS.keys()]


async def calculate_dynamic_interval(price_history: List[Dict[str, Any]]) -> int:
    """Calculate a dynamic interval based on market conditions."""
    if not price_history or len(price_history) < 10:
        return INTERVAL_MINUTES  # Not enough data, use default
    
    # Extract prices
    prices = [entry["price"] for entry in price_history]
    
    # Get latest trend
    trend = detect_price_trend(prices)
    
    # Adjust interval based on trend
    if trend == "strong_buy":
        # More frequent during strong buying opportunities
        return max(15, INTERVAL_MINUTES // 2)
    elif trend == "buy":
        return max(30, int(INTERVAL_MINUTES * 0.7))
    elif trend == "volatile":
        # More frequent during high volatility
        return max(20, INTERVAL_MINUTES // 2)
    elif trend == "sell" or trend == "strong_sell":
        # Less frequent during selling conditions
        return min(240, INTERVAL_MINUTES * 2)
    else:
        return INTERVAL_MINUTES  # Default interval


# ================== UI Functions ==================

def create_dividend_panel(current_stake: float, excess: float, required_excess: float, next_check: timedelta) -> Panel:
    panel_width = (console.width // 2)

    table = Table.grid(padding=(0, 0))
    table.add_column(justify="left", style=header_style, width=panel_width // 2)
    table.add_column(justify="right", style=value_style, width=panel_width // 2)

    table.add_row("Current Stake:", f"{current_stake:.5f} TAO")
    table.add_row("Minimum Stake:", f"{MIN_ROOT_STAKE:.5f} TAO")
    table.add_row("Current Excess:", f"[cyan]{excess:.5f} TAO[/cyan]")
    table.add_row("Required Excess:", f"{required_excess:.5f} TAO")
    table.add_row("")
    mins, secs = divmod(next_check.seconds, 60)
    table.add_row("Next Update In:", f"{mins}m {secs}s")
    status = "Active" if excess >= required_excess else "Waiting"
    table.add_row("Status:", f"[{'green' if status=='Active' else 'yellow'}]{status}[/{'green' if status=='Active' else 'yellow'}]")

    return Panel(
        table,
        title="[bold magenta]Dividend Management[/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(1, 2),
        width=panel_width,
        height=12
    )


def create_staking_panel(next_staking: datetime, balance: float, total_required: float, price_trend: str = "neutral") -> Panel:
    panel_width = (console.width // 2)

    table = Table.grid(padding=(0, 0))
    table.add_column(justify="left", style=header_style, width=panel_width // 2)
    table.add_column(justify="right", style=value_style, width=panel_width // 2)

    table.add_row("Next Staking:", next_staking.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("Current Balance:", f"{balance:.5f} TAO")
    table.add_row("Required Total:", f"{total_required:.5f} TAO")
    
    # Color-code the trend
    trend_color = {
        "strong_buy": "bright_green",
        "buy": "green",
        "neutral": "white",
        "sell": "yellow",
        "strong_sell": "red",
        "volatile": "magenta"
    }.get(price_trend, "white")
    
    table.add_row("Market Trend:", f"[{trend_color}]{price_trend.replace('_', ' ').title()}[/{trend_color}]")
    
    status = "Ready" if balance >= total_required else "Insufficient"
    table.add_row("Funding Status:", f"[{'green' if status=='Ready' else 'red'}]{status}[/{'green' if status=='Ready' else 'red'}]")

    return Panel(
        table,
        title="[bold green]Dynamic Staking[/bold green]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
        width=panel_width,
        height=12
    )


def create_subnet_panel(subnet_stakes: Dict[int, float], subnet_apys: Dict[int, float]) -> Panel:
    table = Table(title="Subnet Allocations", box=box.ROUNDED, show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Subnet", justify="right", style="cyan")
    table.add_column("Validator", style="white", width=12)
    table.add_column("Staked", justify="right", style="bold green")
    table.add_column("APY", justify="right", style="yellow")
    table.add_column("Status", justify="center", style="white")
    
    for netuid, (_, hotkey) in SUBNET_CONFIGS.items():
        stake = subnet_stakes.get(netuid, 0.0)
        apy = subnet_apys.get(netuid, 0.0)
        saturation = subnet_saturation.get(netuid, {}).get("ratio", 0)
        
        # Determine status indicator
        status = ""
        if saturation > SUBNET_SATURATION_THRESHOLD:
            status = "[red]Saturated[/red]"
        elif apy > 50:
            status = "[bright_green]High APY[/bright_green]"
        elif netuid in [k for k, _ in sorted(subnet_apys.items(), key=lambda x: x[1], reverse=True)[:3]]:
            status = "[cyan]Top APY[/cyan]"
        
        # Truncate hotkey for display
        short_hotkey = f"{hotkey[:6]}...{hotkey[-4:]}"
        
        table.add_row(
            str(netuid),
            short_hotkey,
            f"{stake:.5f} TAO",
            f"{apy:.2f}%" if apy > 0 else "N/A",
            status
        )
    
    return Panel(table, title="[bold blue]Subnet Intelligence[/bold blue]", border_style="blue", box=box.ROUNDED, padding=(1, 1))


def create_history_panel(history: List[str]) -> Panel:
    table = Table(show_header=False, box=box.ROUNDED, expand=True)
    table.add_column("Event", style="white")
    
    for entry in history[-10:]:
        table.add_row(entry)
    
    return Panel(table, title="[bold]Operation History[/bold]", border_style="yellow", box=box.ROUNDED, padding=(1, 1))


def create_strategy_panel(metrics: Dict[str, int], price_data: List[Dict[str, Any]]) -> Panel:
    table = Table(box=box.ROUNDED, expand=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white", justify="right")

    # Add price metrics if available
    if price_data and len(price_data) > 1:
        current_price = price_data[-1]["price"]
        previous_price = price_data[-2]["price"]
        price_change = ((current_price / previous_price) - 1) * 100
        table.add_row(
            "Current TAO Price",
            f"${current_price:.2f} ({price_change:+.2f}%)",
        )
    else:
        table.add_row("Current TAO Price", "Loading...")

    # Add strategy metrics
    for key, value in metrics.items():
        formatted_key = key.replace("_", " ").title()
        table.add_row(formatted_key, str(value))

    return Panel(table, title="[bold cyan]Strategy Metrics[/bold cyan]", border_style="cyan", box=box.ROUNDED, padding=(1, 1))


def create_alerts_panel() -> Panel:
    table = Table(box=box.ROUNDED, expand=True)
    table.add_column("Type", style="yellow", width=12)
    table.add_column("Alert", style="white")

    # Add most recent alerts from each category
    if price_alerts:
        table.add_row("Price", price_alerts[-1])
    
    if validator_alerts:
        table.add_row("Validator", validator_alerts[-1])
    
    if apy_alerts:
        table.add_row("APY", apy_alerts[-1])

    return Panel(table, title="[bold red]Active Alerts[/bold red]", border_style="red", box=box.ROUNDED, padding=(1, 1))


# ================== Main Staking Logic ==================

async def staking_manager(subtensor: bt.AsyncSubtensor, wallet: bt.wallet, live: Live) -> None:
    """
    Main staking manager that coordinates all the advanced strategies.
    
    This function orchestrates:
    - Dynamic DCA based on price trends
    - Front-running validator movements
    - Volatility-adjusted staking windows
    - High-yield subnet rotation
    - Subnet saturation avoidance
    """
    coldkey = wallet.coldkeypub.ss58_address
    root_hotkey = ROOT_HOTKEY
    total_required = sum(amount for amount, _ in SUBNET_CONFIGS.values())
    
    # Initialize timers and trackers
    last_div_check = datetime.utcnow()
    last_price_check = datetime.utcnow() - PRICE_CHECK_INTERVAL  # Check immediately
    last_validator_check = datetime.utcnow() - VALIDATOR_TRACK_INTERVAL  # Check immediately
    last_apy_check = datetime.utcnow() - APY_CHECK_INTERVAL  # Check immediately
    
    # Initialize data holders
    current_stake = await get_stake(subtensor, coldkey, root_hotkey, ROOT_NETUID)
    balance = await get_balance(subtensor, wallet.coldkeypub.ss58_address)
    excess = current_stake.tao - MIN_ROOT_STAKE
    required_excess = MIN_STAKE_THRESHOLD * len(SUBNET_CONFIGS)
    next_div_check = last_div_check + DIVIDEND_CHECK_INTERVAL
    time_until_div = next_div_check - datetime.utcnow()
    
    subnet_stakes = {netuid: 0.0 for netuid in SUBNET_CONFIGS.keys()}
    subnet_apys = {netuid: 0.0 for netuid in SUBNET_CONFIGS.keys()}
    current_price_trend = "neutral"
    
    # Load schedule
    schedule = read_schedule()
    next_staking = schedule["next_staking"]
    interval_minutes = schedule["interval_minutes"]
    dynamic_interval = schedule.get("dynamic_interval", True)
    
    # Load price history
    price_history = read_price_history()
    
    # Check and update interval
    if interval_minutes != INTERVAL_MINUTES and not dynamic_interval:
        console.print("[yellow]⚠️ Interval changed; recalculating next staking time[/yellow]")
        next_staking = next_staking_time(interval_minutes=interval_minutes)
        append_history("Interval changed; recalculating next staking time")
    
    # Check if we missed a scheduled staking
    if next_staking is None or datetime.utcnow() > next_staking:
        console.print("[yellow]⚠️ Recalculating from missed schedule [/yellow]")
        next_staking = next_staking_time(interval_minutes=interval_minutes)
        append_history("Recalculating from missed schedule")
    
    # Function to update the dashboard
    async def update_dashboard():
        nonlocal current_stake, balance, excess, required_excess, next_div_check, time_until_div
        nonlocal next_staking, current_price_trend
        
        try:
            # Update core data
            current_stake = await get_stake(subtensor, coldkey, root_hotkey, ROOT_NETUID)
            balance = await get_balance(subtensor, wallet.coldkeypub.ss58_address)
            
            # Update subnet stakes
            for netuid in SUBNET_CONFIGS:
                stake = await get_stake(subtensor, coldkey, SUBNET_CONFIGS[netuid][1], netuid)
                subnet_stakes[netuid] = stake.tao
            
            # Update excess calculations
            excess = current_stake.tao - MIN_ROOT_STAKE
            required_excess = MIN_STAKE_THRESHOLD * len(SUBNET_CONFIGS)
            next_div_check = last_div_check + DIVIDEND_CHECK_INTERVAL
            time_until_div = next_div_check - datetime.utcnow()
            
            # Get price trend if we have data
            if price_history:
                prices = [entry["price"] for entry in price_history]
                current_price_trend = detect_price_trend(prices)
            
            # Create dashboard panels
            dividend_panel = create_dividend_panel(current_stake.tao, excess, required_excess, time_until_div)
            staking_panel = create_staking_panel(next_staking, balance.tao, total_required, current_price_trend)
            subnet_panel = create_subnet_panel(subnet_stakes, subnet_apys)
            history_panel = create_history_panel(history_log)
            strategy_panel = create_strategy_panel(strategy_metrics, price_history)
            alerts_panel = create_alerts_panel()
            
            # Arrange panels in grid
            top_row = Columns(
                [dividend_panel, staking_panel],
                equal=True,
                expand=False,
                padding=0,
                align="left"
            )
            
            middle_row = Columns(
                [strategy_panel, alerts_panel],
                equal=True,
                expand=False,
                padding=0,
                align="left"
            )
            
            dashboard = Group(
                top_row,
                middle_row,
                subnet_panel,
                history_panel
            )
            
            live.update(dashboard)
            
        except Exception as e:
            logger.error(f"Dashboard update failed: {e}")
            live.update(Panel(
                f"[red]Dashboard update failed: {str(e)}[/red]",
                title="[bold]Enhanced DCA Script[/bold]",
                border_style="red",
                box=box.ROUNDED
            ))
    
    # Initialize dashboard
    dashboard = Group(
        create_dividend_panel(current_stake.tao, excess, required_excess, timedelta(0)),
        create_staking_panel(next_staking, balance.tao, total_required, "neutral"),
        create_subnet_panel(subnet_stakes, subnet_apys),
        create_history_panel(history_log)
    )
    live.update(dashboard)
    
    # Main loop
    while True:
        try:
            # Update dashboard
            await update_dashboard()
            
            # Check TAO price at interval
            if datetime.utcnow() >= last_price_check + PRICE_CHECK_INTERVAL:
                price = await fetch_tao_price()
                if price is not None:
                    timestamp = datetime.utcnow().isoformat()
                    price_history.append({
                        "timestamp": timestamp,
                        "price": price
                    })
                    
                    # Keep history manageable (last 30 days)
                    while len(price_history) > 8640:  # 30 days at 5-minute intervals
                        price_history.pop(0)
                    
                    # Save updated price history
                    write_price_history(price_history)
                    
                    # Update price trend
                    prices = [entry["price"] for entry in price_history]
                    if len(prices) >= 5:
                        current_price_trend = detect_price_trend(prices)
                        
                        # Log significant price movements
                        if current_price_trend in ["strong_buy", "strong_sell"]:
                            append_price_alert(f"TAO Price: ${price:.2f} - {current_price_trend.replace('_', ' ').title()}")
                    
                    # Check for dynamic interval adjustment if enabled
                    if dynamic_interval and len(price_history) >= 10:
                        new_interval = await calculate_dynamic_interval(price_history)
                        if new_interval != interval_minutes:
                            interval_minutes = new_interval
                            next_staking = next_staking_time(interval_minutes=interval_minutes)
                            write_schedule(next_staking, interval_minutes, dynamic_interval)
                            append_history(f"Adjusted interval to {interval_minutes} minutes based on market")
                
                last_price_check = datetime.utcnow()
            
            # Check validator movements
            if datetime.utcnow() >= last_validator_check + VALIDATOR_TRACK_INTERVAL:
                frontrun_opportunities = await analyze_validator_movements(subtensor)
                if any(frontrun_opportunities.values()):
                    active_opportunities = [netuid for netuid, active in frontrun_opportunities.items() if active]
                    append_validator_alert(f"Validator activity detected on subnets: {', '.join(map(str, active_opportunities))}")
                
                last_validator_check = datetime.utcnow()
            
            # Check APY updates
            if datetime.utcnow() >= last_apy_check + APY_CHECK_INTERVAL:
                subnet_apys = await calculate_subnet_apys(subtensor)
                
                # Get top APY subnets (excluding saturated)
                top_subnets = await get_top_apy_subnets(subnet_apys, excluding_saturated=True)
                if top_subnets:
                    top_apy_msg = f"Top APY subnets: {', '.join(map(str, top_subnets))}"
                    append_apy_alert(top_apy_msg)
                    
                    # Check for rotation opportunities
                    current_top_apys = [subnet_apys.get(netuid, 0) for netuid in top_subnets]
                    other_subnets = [n for n in SUBNET_CONFIGS.keys() if n not in top_subnets]
                    other_apys = [subnet_apys.get(netuid, 0) for netuid in other_subnets]
                    
                    if current_top_apys and other_apys:
                        top_avg = sum(current_top_apys) / len(current_top_apys)
                        other_avg = sum(other_apys) / len(other_apys) if other_apys else 0
                        
                        if top_avg > other_avg * (1 + APY_ROTATION_THRESHOLD):
                            append_apy_alert(f"APY rotation suggested: {top_avg:.2f}% vs {other_avg:.2f}%")
                            strategy_metrics["apy_rotations"] += 1
                
                last_apy_check = datetime.utcnow()
            
            # Process dividend checks
            if datetime.utcnow() >= last_div_check + DIVIDEND_CHECK_INTERVAL:
                if current_stake.tao > MIN_ROOT_STAKE and excess >= required_excess:
                    # Get market conditions before unstaking
                    should_adjust, volatility_factor = await should_adjust_for_volatility(price_history)
                    
                    if should_adjust:
                        adjusted_excess = excess * volatility_factor
                        append_history(f"Volatility adjustment: {volatility_factor:.2f}x factor")
                    else:
                        adjusted_excess = excess
                    
                    # Determine best subnets to stake on
                    ranked_subnets = await determine_best_subnets(subtensor)
                    
                    # Unstake from root
                    actual_unstaked = await unstake_excess(subtensor, wallet, ROOT_NETUID, root_hotkey, adjusted_excess)
                    
                    if actual_unstaked > 0:
                        # Calculate proportional allocations based on subnet rankings
                        total_score = sum(score for _, score in ranked_subnets)
                        subnet_allocations = {}
                        
                        if total_score > 0:
                            for netuid, score in ranked_subnets:
                                subnet_allocations[netuid] = (actual_unstaked * score / total_score)
                        else:
                            # Fallback to equal distribution
                            for netuid in SUBNET_CONFIGS.keys():
                                subnet_allocations[netuid] = actual_unstaked / len(SUBNET_CONFIGS)
                        
                        # Process each subnet with its calculated allocation
                        successful_subnets = 0
                        for netuid, amount in subnet_allocations.items():
                            if amount >= MIN_STAKE_THRESHOLD:
                                try:
                                    hotkey = SUBNET_CONFIGS[netuid][1]
                                    await process_subnet(subtensor, wallet, netuid, amount, hotkey)
                                    successful_subnets += 1
                                    await update_dashboard()
                                    await asyncio.sleep(0)
                                except Exception as e:
                                    logger.error(f"Subnet {netuid} processing failed: {e}")
                                    append_history(f"Subnet {netuid} distribution failure")
                        
                        # Log results
                        efficiency = (successful_subnets / len(SUBNET_CONFIGS) * 100)
                        append_history(f"Distributed {actual_unstaked:.5f} TAO (Coverage: {efficiency:.1f}%)")
                        strategy_metrics["dca_triggers"] += 1
                    else:
                        append_history("No funds available for distribution")
                else:
                    append_history("Dividend check - insufficient excess")
                
                last_div_check = datetime.utcnow()
            
            # Check for scheduled staking
            if datetime.utcnow() >= next_staking:
                # Check if we have sufficient balance
                if balance.tao >= total_required:
                    # Check if it's an optimal time to stake
                    is_optimal = await determine_optimal_staking_time(price_history)
                    
                    if is_optimal:
                        # Front-run validator movements
                        frontrun_opportunities = await analyze_validator_movements(subtensor)
                        ranked_subnets = await determine_best_subnets(subtensor)
                        
                        # Calculate dynamic allocation
                        allocation = {}
                        total_score = sum(score for _, score in ranked_subnets)
                        
                        if total_score > 0:
                            # Adjust allocations based on rankings
                            for netuid, (base_amount, _) in SUBNET_CONFIGS.items():
                                subnet_score = next((score for net, score in ranked_subnets if net == netuid), 1.0)
                                allocation[netuid] = base_amount * (1 + (subnet_score / total_score))
                            
                            # Normalize to match total required
                            allocation_total = sum(allocation.values())
                            scale_factor = total_required / allocation_total
                            
                            for netuid in allocation:
                                allocation[netuid] *= scale_factor
                        else:
                            # Default to base configuration
                            for netuid, (amount, _) in SUBNET_CONFIGS.items():
                                allocation[netuid] = amount
                        
                        # Execute staking with calculated allocations
                        for netuid, amount in allocation.items():
                            if netuid in subnet_saturation and subnet_saturation[netuid].get("is_saturated", False):
                                append_history(f"Skipping saturated subnet {netuid}")
                                continue
                                
                            hotkey = SUBNET_CONFIGS[netuid][1]
                            await process_subnet(subtensor, wallet, netuid, amount, hotkey)
                        
                        # Calculate next staking time
                        new_next = next_staking_time(interval_minutes=interval_minutes)
                        write_schedule(new_next, interval_minutes, dynamic_interval)
                        next_staking = new_next
                        append_history(f"Scheduled stake completed. Next at {new_next.strftime('%H:%M UTC')}")
                    else:
                        # Delay staking due to market conditions
                        delay_minutes = max(30, interval_minutes // 4)
                        next_staking = datetime.utcnow() + timedelta(minutes=delay_minutes)
                        write_schedule(next_staking, interval_minutes, dynamic_interval)
                        append_history(f"Staking delayed {delay_minutes}m due to market conditions")
                        append_price_alert(f"Staking postponed: unfavorable conditions ({current_price_trend})")
                else:
                    # Insufficient balance, postpone
                    delay_minutes = 60
                    next_staking = datetime.utcnow() + timedelta(minutes=delay_minutes)
                    write_schedule(next_staking, interval_minutes, dynamic_interval)
                    append_history(f"Insufficient balance for scheduled staking. Delayed {delay_minutes}m")
            
            # Short sleep to prevent CPU spinning
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Manager error: {str(e)}")
            live.update(Panel(
                f"[red]Error occurred: {str(e)} - check logs[/red]",
                title="[bold]Enhanced DCA Script[/bold]",
                border_style="red",
                box=box.ROUNDED
            ))
            append_history(f"Error in manager: {str(e)}")
            await asyncio.sleep(10)
            
async def main():
    subtensor = bt.subtensor('local')
    wallet = bt.wallet()
    wallet.unlock_coldkey()
    
    with Live(Group(), refresh_per_second=1) as live:
        await staking_manager(subtensor, wallet, live)

if __name__ == '__main__':
    # Run the async main function
    asyncio.run(main())
    
    