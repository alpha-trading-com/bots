import time
import bittensor as bt
from utils.utils import *

default_delta_price = 0.0005
stake_amount = 0.1

def stake_cheat1(netuid, subtensor, wallet, hotkey, tao_amount):
    staked = stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
    current_price = exchange_rates(netuid, subtensor)
    staked_price = current_price
    while True:
        try:
            alpha_to_tao = exchange_rates(netuid, subtensor)
            print(f"==== Current price: {current_price} ====")
            print(f"==== Staked price: {staked_price} ====")
            print(f"==== Alpha to tao: {alpha_to_tao} ====")
            print(f"==== Staked: {staked} ====")
            if alpha_to_tao > current_price:
                current_price = alpha_to_tao
            elif alpha_to_tao == current_price:
                print("No change in price")
            elif staked:
                if staked_price < alpha_to_tao:
                    result = unstake_from_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
                    current_price = exchange_rates(netuid, subtensor)
                    if result:
                        staked_price = current_price
                        staked = False
                    else:
                        print("Failed to unstake")
                else:
                    print("staked_price is greater than alpha_to_tao, no unstake")
                
            elif not staked:
                if staked_price > alpha_to_tao:
                    staked = stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
                    current_price = exchange_rates(netuid, subtensor)
                    if staked:
                        staked_price = current_price
                    else:
                        print("Failed to stake")
                else:
                    print("staked_price is less than alpha_to_tao, no stake")
            else:
                print("No change in price")
            
            get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
            subtensor.wait_for_block()

            time.sleep(60)
        except Exception as e:
            print(f"=== Unexpected Error: {e} ===")

def stake_cheat2(netuid, subtensor, wallet, hotkey, tao_amount):
    staked = stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
    staked_price = exchange_rates(netuid, subtensor)
    subtensor.wait_for_block()
    time.sleep(60)
    while True:
        try:
            alpha_to_tao = exchange_rates(netuid, subtensor)
            print(f"==== Staked price: {staked_price} ====")
            print(f"==== Alpha to tao: {alpha_to_tao} ====")
            print(f"==== Staked: {staked} ====")
            if alpha_to_tao > staked_price + default_delta_price:
                if staked:
                    unstake_from_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
                    staked_price = exchange_rates(netuid, subtensor)
                    staked = False
                else:
                    # stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
                    # staked_price = exchange_rates(netuid, subtensor)
                    # staked = True
                    pass
            elif alpha_to_tao == staked_price:
                print("No change in price")
            elif alpha_to_tao < staked_price - default_delta_price:
                if not staked:
                    staked = stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
                    staked_price = exchange_rates(netuid, subtensor)
                else:
                    print("Already staked")

            get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
            subtensor.wait_for_block()
            time.sleep(60)
        except Exception as e:
            print(f"=== Unexpected Error: {e} ===")

if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    hotkey = input("Enter the hotkey: ")

    # Create a wallet instance
    wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
    wallet.unlock_coldkey()
    
    subtensor = bt.subtensor('finney')

    # Register the wallet to the subnet
    # stake_cheat1(4, subtensor, wallet, "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1", 0.1)
    
    # unstake_from_subnet(4, subtensor, wallet, "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1", 0.1)
    
    stake_cheat2(netuid, subtensor, wallet, "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1", stake_amount)