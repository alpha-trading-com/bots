from twitter_bot.twitter_bot import TwitterBot


import os
import bittensor as bt
from typing import Dict
from dotenv import load_dotenv
import argparse


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

def stake(
    tao_amount: float, 
    netuid: int, 
    wallet_name: str, 
    dest_hotkey: str = ROUND_TABLE_HOTKEY, 
    rate_tolerance: float = 0.005,
    min_tolerance_staking: bool = True,
    retries: int = 20,
):
    if retries < 1:
        retries = 1
    result = None
    min_tolerance = None
    while retries > 0:
        try:
            wallet = wallets[wallet_name]
            subtensor = bt.subtensor(network=NETWORK)
            subnet = subtensor.subnet(netuid=netuid)
            min_tolerance = tao_amount / subnet.tao_in.tao  
            if min_tolerance_staking:
                rate_tolerance = min_tolerance + min_tolerance

            result = subtensor.add_stake(
                netuid=netuid,
                amount= bt.Balance.from_tao(tao_amount, netuid),
                wallet=wallet,
                hotkey_ss58=dest_hotkey,
                safe_staking=True,
                rate_tolerance=rate_tolerance
            )
            if not result:
                raise Exception("Stake failed")
            
            return {
                "success": True,
                "result": result,
                "min_tolerance": min_tolerance,
            }
        except Exception as e:
            retries -= 1
            if retries == 0:
                return {
                    "success": False,
                    "result": result,
                    "min_tolerance": min_tolerance,
                }

def unstake(
    netuid: int,
    wallet_name: str,
    amount: float = None,
    dest_hotkey: str = ROUND_TABLE_HOTKEY,
    retries: int = 20,
):
    if retries < 1:
        retries = 1
    result = None
    while retries > 0:
        try:

            wallet = wallets[wallet_name]
            subtensor = bt.subtensor(network=NETWORK)
            if amount is not None:
                subnet = subtensor.subnet(netuid=netuid)
                amount = bt.Balance.from_tao(amount / subnet.price.tao, netuid)

            result = subtensor.unstake(
                netuid=netuid, 
                wallet=wallet, 
                amount=amount,
                hotkey_ss58=dest_hotkey,
            )
            if not result:
                raise Exception("Unstake failed")
            
            return {
                "success": True,
                "result": result,
            }
        except Exception as e:
            retries -= 1
            if retries == 0:
                return {
                    "success": False,
                    "result": result,
                }



def stake_callback(subnet):
    print(f"Subnet {subnet} found in tweet")
    stake(100, subnet, "stake_2")


def unstake_callback(subnet):
    if subnet != 54:
        unstake(subnet, "sec_ck4")

    if subnet != 47:
        unstake(subnet, "stake_2")

    if subnet != 69:
        unstake(subnet, "stake_2")
    

if __name__ == "__main__":

    unlock_wallets()
    bot = TwitterBot()
    username = "OpenGradient"
    print(f"Starting to monitor tweets from @{username}...")

    parser = argparse.ArgumentParser()
    parser.add_argument('--stake', action='store_true', help='Stake mode')
    parser.add_argument('--unstake', action='store_true', help='Unstake mode')
    args = parser.parse_args()

    if args.stake:
        bot.check_new_tweets(username, stake_callback)
    elif args.unstake:
        bot.check_new_tweets(username, unstake_callback)
    else:
        print("Please specify either --stake or --unstake")
        exit(1)
    