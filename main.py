import time
import bittensor as bt
from utils.utils import *

default_delta_price = 0.0005
stake_amount = 0.1

def stake_cheat2(netuid, subtensor, wallet, hotkey, tao_amount):
    get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
    staked = stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
    staked_price = exchange_rates(netuid, subtensor)
    middel_price = staked_price
    staked_float = float(str(staked_price).replace('τ', ''))
    get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
    subtensor.wait_for_block()
    time.sleep(60)
    while True:
        try:
            alpha_to_tao = exchange_rates(netuid, subtensor)
            alpha_float = float(str(alpha_to_tao).replace('τ', ''))
            print(f"==== Staked price: {staked_float} ====")
            print(f"==== Alpha to tao: {alpha_float} ====")
            print(f"==== Netuid: {netuid} | Staked: {staked} ====")
            if alpha_float > staked_float + default_delta_price:
                if staked:
                    unstaked = unstake_from_subnet(netuid, subtensor, wallet, hotkey)
                    if unstaked:
                        staked_price = exchange_rates(netuid, subtensor)
                        staked_float = float(str(staked_price).replace('τ', ''))
                        staked = False
                        get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
                    else:
                        print("Failed to unstake")
                else:
                    pass
            elif alpha_float == staked_float:
                print("No change in price")
            elif alpha_float < staked_float - default_delta_price and middel_price > alpha_float:
                if not staked:
                    staked = stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
                    if staked:
                        staked_price = exchange_rates(netuid, subtensor)
                        staked_float = float(str(staked_price).replace('τ', ''))
                        get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
                    else:
                        print("Failed to stake")
                else:
                    print("Already staked")

            middel_price = alpha_float
            subtensor.wait_for_block()
            time.sleep(60)
        except Exception as e:
            print(f"=== Unexpected Error: {e} ===")

if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    user_stake_amount = float(input("Enter the stake amount: "))
    hotkey = input("Enter the hotkey: ")

    # Create a wallet instance
    wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
    wallet.unlock_coldkey()
    
    subtensor = bt.subtensor('local')

    stake_cheat2(netuid, subtensor, wallet, "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1", user_stake_amount)