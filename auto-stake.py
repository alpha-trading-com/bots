import time
import bittensor as bt
from utils.const import sn_vali_addr
from utils.utils import *


def autoStake(netuid, subtensor, wallet, hotkey, tao_amount):
    get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
    
    for i in range(100):
        logger.info(f"=== [{i}] Staking {tao_amount} TAO to subnet {netuid} ===")
        staked = stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
        get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
        subtensor.wait_for_block()
        time.sleep(1200)
        
if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    hotkey = input("Enter the hotkey: ")
    user_stake_amount = float(input("Enter the stake amount: "))
    
    subtensor = bt.subtensor('local')
    
    # Create a wallet instance
    wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
    wallet.unlock_coldkey()
    
    autoStake(netuid, subtensor, wallet, sn_vali_addr(netuid), user_stake_amount)