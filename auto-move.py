import time
import bittensor as bt
import argparse
from utils.utils import *

default_delta_price = 0.00001
stake_amount = 1

def auto_move(netuid, subtensor, wallet, hotkey, dest_hotkey, tao_amount):
    while True:
        try:
            unstake_from_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
            stake_to_subnet(netuid, subtensor, wallet, dest_hotkey, tao_amount)
            subtensor.wait_for_block()
            time.sleep(5)
            print(f"==== sleeping... ====")
        except Exception as e:
            print(f"=== Unexpected Error: {e} ===")

if __name__ == '__main__':
    # Create a wallet instance
    wallet = bt.wallet(name='sec_ck1', hotkey='hk1')
    wallet.unlock_coldkey()
    
    print(wallet.hotkey.ss58_address)
    
    subtensor = bt.subtensor('finney')

    auto_move(54, subtensor, wallet, wallet.hotkey.ss58_address, "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v", 1)
    
