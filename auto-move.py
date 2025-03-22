import time
import bittensor as bt
import argparse
from utils.const import sn_vali_addr
from utils.utils import *

default_delta_price = 0.00001
stake_amount = 1

def auto_move(netuid, subtensor, wallet, dest_hotkey, tao_amount):
    hotkey1 = "5EFsCTK1Ao6aAgG6KcfHFeoH693vdiT2bwwE3Rmn2drG4yd2"
    hotkey2 = "5CfBpgAk4AUTBNFt43QpLr39bYpGB52pBcB9qhp9oqpaGtYr"
    while True:
        try:
            unstaked = unstake_from_subnet(netuid, subtensor, wallet, hotkey1, tao_amount)
            logger.info(f"unstaked[1]: {unstaked}")
            if unstaked:
                stake_to_subnet(netuid, subtensor, wallet, dest_hotkey, tao_amount)
            time.sleep(60)
            
            unstaked = unstake_from_subnet(netuid, subtensor, wallet, hotkey2, tao_amount)
            logger.info(f"unstaked[2]: {unstaked}")
            if unstaked:
                stake_to_subnet(netuid, subtensor, wallet, dest_hotkey, tao_amount)

            subtensor.wait_for_block()
            time.sleep(600)
            logger.info("==== sleeping... ====")
        except Exception as e:
            logger.error(f"=== Unexpected Error: {e} ===")
            subtensor.wait_for_block()
            time.sleep(60)
            

if __name__ == '__main__':
    # Create a wallet instance
    wallet = bt.wallet(name='sec_ck1', hotkey='hk2')
    wallet.unlock_coldkey()
    
    logger.info(wallet.hotkey.ss58_address)
    
    subtensor = bt.subtensor('local')

    auto_move(54, subtensor, wallet, sn_vali_addr(54), 0.1)
    
