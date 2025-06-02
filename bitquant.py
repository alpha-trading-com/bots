from twitter_bot.twitter_bot import TwitterBot


import os
import bittensor as bt
from typing import Dict
from dotenv import load_dotenv
import asyncio

from constants import ROUND_TABLE_HOTKEY, NETWORK

load_dotenv()
wallet_names = os.getenv('WALLET_NAMES', '').split(',')
wallets: Dict[str, bt.wallet] = {}

def unlock_wallets():
    for wallet_name in wallet_names:
        wallet = bt.wallet(name=wallet_name)
        print(f"Unlocking wallet {wallet_name}")
        wallet.unlock_coldkey()
        wallets[wallet_name] = wallet

async def stake(
    tao_amount: float, 
    netuid: int, 
    wallet_name: str, 
    dest_hotkey: str = ROUND_TABLE_HOTKEY, 
    rate_tolerance: float = 0.005,
    min_tolerance_staking: bool = True,
    retries: int = 20,
):
    while retries > 0:
        try:
            wallet = wallets[wallet_name]
            subtensor = bt.async_subtensor(network=NETWORK)
            subnet = await subtensor.subnet(netuid=netuid)
            min_tolerance = tao_amount / subnet.tao_in.tao  
            if min_tolerance_staking:
                rate_tolerance = min_tolerance + min_tolerance

            result = await subtensor.add_stake(
                netuid=netuid,
                amount= bt.Balance.from_tao(tao_amount, netuid),
                wallet=wallet,
                hotkey_ss58=dest_hotkey,
                safe_staking=True,
                rate_tolerance=rate_tolerance
            )
            if not result:
                raise Exception("Stake failed")
            
        except Exception as e:
            retries -= 1
            if retries == 0:
                break

async def unstake(
    netuid: int,
    wallet_name: str,
    dest_hotkey: str = ROUND_TABLE_HOTKEY,
    retries: int = 20,
):
    while retries > 0:
        try:
            wallet = wallets[wallet_name]
            subtensor = bt.async_subtensor(network=NETWORK)
            result = await subtensor.unstake(
                netuid=netuid, 
                wallet=wallet, 
                hotkey_ss58=dest_hotkey,
            )
            if not result:
                raise Exception("Unstake failed")
        except Exception as e:
            retries -= 1
            if retries == 0:
                break


async def async_callback(subnet):
    print(f"Subnet {subnet} found in tweet")
    tasks = []
    tasks.append(stake(amount=200, netuid=subnet, wallet_name="stake_2"))

    if subnet != 54:
        tasks.append(unstake(netuid=subnet, wallet_name="sec_ck4", dest_hotkey="5CPR71gqPyvBT449xpezgZiLpxFaabXNLmnfcQdDw2t3BwqC"))

    if subnet != 47:
        tasks.append(unstake(netuid=subnet, wallet_name="stake_2"))

    if subnet != 69:
        tasks.append(unstake(netuid=subnet, wallet_name="stake_2"))

    await asyncio.gather(*tasks)


def callback(subnet):
    asyncio.run(async_callback(subnet))


if __name__ == "__main__":

    unlock_wallets()
    bot = TwitterBot()
    username = "OpenGradient"
    print(f"Starting to monitor tweets from @{username}...")
    bot.check_new_tweets(username, callback)
    