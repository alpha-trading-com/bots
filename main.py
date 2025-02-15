import bittensor as bt
from utils.utils import *

def stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount):
    exchange_rates(netuid, subtensor)
    get_balance_coldkey(subtensor, "5EHx75t5ukKKG3wB6k8kVpybigsf1mqbKZ9hfvEbA3QD48qP")
    stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)

if __name__ == '__main__':
    # netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    hotkey = input("Enter the hotkey: ")

    # # Create a wallet instance
    wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
    wallet.unlock_coldkey()
    
    subtensor = bt.subtensor('finney')

    # Register the wallet to the subnet
    # old_register(netuid, subtensor, wallet)
    stake_to_subnet(4, subtensor, wallet, "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1", 1000000000000000000)