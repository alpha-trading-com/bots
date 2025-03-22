import bittensor as bt
from utils.utils import *
from utils.const import sn_vali_addr

def stake_cheat1(netuid, subtensor, wallet, hotkey, tao_amount):
    get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
    # stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
    # get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
    # unstake_from_subnet(netuid, subtensor, wallet, hotkey)
    # get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)

if __name__ == '__main__':
    logger.info(f"==== started ====")
    # netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    hotkey = input("Enter the hotkey: ")
    # user_stake_amount = float(input("Enter the stake amount: "))
    
    subtensor = bt.subtensor('local')

    wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
    wallet.unlock_coldkey()

    logger.info(f"==== get balance of {wallet.coldkeypub.ss58_address} ====")
    get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)

    # stake_cheat1(netuid, subtensor, wallet, sn_vali_addr(netuid), user_stake_amount)