import time
import bittensor as bt
import argparse
from utils.utils import *
from constants import NETWORK

default_delta_price = 0.00001
stake_amount = 1

def auto_stake_move(netuid, subtensor, wallet, dest_hotkey, alpha_amount):
    hotkey1 = "5GxHLxZDntjf8dbwJEKMXR2NvGckoJUapc7Gsj3bBbA96nf9"
    hotkey2 = "5FqPndsB4VnYuPf73RcDqmsLiAnHcJZLUXfvyd8M476643fH"
    hotkey3 = "5EveXqcAc85GzXWiXnmnDstd4Hx5Kpo8Hw58BPGQqpU7dFnq"
    hotkey4 = "5HDtQiPjdCPhM8zh5Jv6bfKLJNu3mESXJBGaebEzYF3NRmyu"
    hotkey5 = "5FCxQ1kv4q3tgiTMUH7845wDsGho9oGSrmKevpYuRDnWgpgD"
    hotkey6 = "5GGymrP2X64ko3nxLEP4iR3g8rgrQQzeiL4e6VNWiKXgcciZ"
    hotkey7 = "5HC7FMzgpy529kRP9LP2VDwCbJmDQQKRyfUkUDbgjLL3vHkN"
    hotkey8 = "5HH2XtfGxEw8yVeynPFEuVJg2rZPpjBHZY5ubKtUdUzyk85x"
    hotkey9 = "5EhoryScqfDmbzXnpHhdv3rN68yZJvZxQjjeEJgicy9qqCgc"
    while True:
        try:
            move_stake(netuid, subtensor, wallet, hotkey1, alpha_amount, dest_hotkey)
            time.sleep(60)
            subtensor.wait_for_block()
            move_stake(netuid, subtensor, wallet, hotkey2, alpha_amount, dest_hotkey)
            time.sleep(60)
            subtensor.wait_for_block()
            move_stake(netuid, subtensor, wallet, hotkey3, alpha_amount, dest_hotkey)
            time.sleep(60)
            subtensor.wait_for_block()
            move_stake(netuid, subtensor, wallet, hotkey4, alpha_amount, dest_hotkey)
            time.sleep(60)
            subtensor.wait_for_block()  
            move_stake(netuid, subtensor, wallet, hotkey5, alpha_amount, dest_hotkey)
            time.sleep(60)
            subtensor.wait_for_block()
            move_stake(netuid, subtensor, wallet, hotkey6, alpha_amount, dest_hotkey)
            time.sleep(60)
            subtensor.wait_for_block()
            move_stake(netuid, subtensor, wallet, hotkey7, alpha_amount, dest_hotkey)
            time.sleep(60)
            subtensor.wait_for_block()
            move_stake(netuid, subtensor, wallet, hotkey8, alpha_amount, dest_hotkey)
            time.sleep(60)
            subtensor.wait_for_block()
            move_stake(netuid, subtensor, wallet, hotkey9, alpha_amount, dest_hotkey)
            
            logger.info("==== sleeping... ====")
            time.sleep(3600)

        except Exception as e:
            logger.error(f"=== Unexpected Error: {e} ===")
            time.sleep(60)
            

if __name__ == '__main__':
    # Create a wallet instance
    wallet = bt.wallet(name='sec_ck4')
    wallet.unlock_coldkey()
    
    
    subtensor = bt.subtensor(NETWORK)
    src_hotkey = "5GFDSCSaLqAWd7oHxyS4BmETaCwqSkaUeBNoi4zPheYZq95W"
    dest_hotkey = "5CPR71gqPyvBT449xpezgZiLpxFaabXNLmnfcQdDw2t3BwqC"
    netuid = 54
    while True:
        #auto_stake_move(81, subtensor, wallet, sn_vali_addr(81), 10)
        alpha_amount = subtensor.get_stake(coldkey_ss58=wallet.coldkeypub.ss58_address, hotkey_ss58=src_hotkey, netuid=netuid) - 30
        print(f"alpha_amount: {alpha_amount}")
        move_stake(netuid, subtensor, wallet, src_hotkey, alpha_amount, dest_hotkey)
        time.sleep(60 * 2)
