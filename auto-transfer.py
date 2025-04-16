import time
import bittensor as bt
import argparse
from utils.const import sn_vali_addr
from utils.utils import *

default_delta_price = 0.00001
stake_amount = 1

def auto_stake_move(netuid, subtensor, wallet, dest_hotkey, alpha_amount):
    hotkey1 = "5DXD5qbizv5Nct44VwrEYvRvzLRNNjurw2XgM4DtR2kC1FLF"
    hotkey2 = "5G6MYC2iZdqA6atwjVAgw3nyjvmXygJ4GEib9qox2MfWANWc"
    hotkey3 = "5FWq3nMw1MPDx2i4n4bKd4bugjmLPLtYsbBKnU73VeCstCdx"
    hotkey4 = "5D7FwCdKMuthKJ2ctAT1sqNtDMT2HMawYZyuHThrekKGVmc8"
    hotkey5 = "5D2MwaGVq8Zm6UsnmLGM8yg4tybzbwUtjsfNLJfDdXrRbNq1"
    hotkey6 = "5CyZQs1xHzLuvutoeAkh486faH78cZtE3hmiukAcgtMTHsdD"
    hotkey7 = "5GgYL9k1AjaQo6sXAwm5FmkJGQFSkL6opL6oiKkAsREcpGWa"
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
            logger.info("==== sleeping... ====")
            time.sleep(3600)

        except Exception as e:
            logger.error(f"=== Unexpected Error: {e} ===")
            time.sleep(60)
            

if __name__ == '__main__':
    # Create a wallet instance
    wallet = bt.wallet(name='sec_ck3', hotkey='hk2')
    wallet.unlock_coldkey()
    
    logger.info(wallet.hotkey.ss58_address)
    
    subtensor = bt.subtensor('finney')

    auto_stake_move(81, subtensor, wallet, sn_vali_addr(81), 10)
    
