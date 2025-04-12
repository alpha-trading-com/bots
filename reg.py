import bittensor as bt
from utils.utils import *

if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    hotkey = input("Enter the hotkey: ")

    # Create a wallet instance
    wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
    wallet.unlock_coldkey()
    
    subtensor = bt.subtensor('local')

    # Register the wallet to the subnet
    dtao_register(netuid, subtensor, wallet)