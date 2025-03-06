import time
import bittensor as bt
from utils.const import sn_vali_addr
from utils.utils import *

default_delta_price = 0.0005
# stake_amount = 1

def cheat1(netuid, subtensor, wallet, hotkey, tao_amount, entry_price):
    get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
    
    alpha_to_tao = exchange_rates(netuid, subtensor)
    alpha_float = float(str(alpha_to_tao).replace('τ', ''))
    print(f"Alpha to tao: {alpha_float}")
    staked = False
    
    if alpha_float < entry_price:
        staked = stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
        staked_price = exchange_rates(netuid, subtensor)
        staked_float = float(str(staked_price).replace('τ', ''))
        get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
        subtensor.wait_for_block()
        time.sleep(60)
    else:
        staked_float = entry_price + default_delta_price
        print("Alpha to tao is too high, skipping stake")
        time.sleep(60)
        
    while True:
        try:
            alpha_to_tao = exchange_rates(netuid, subtensor)
            alpha_float = float(str(alpha_to_tao).replace('τ', ''))
            print(f"[{netuid} staked: {staked} amount: {tao_amount}] ===> Staked price: {staked_float} || Alpha to tao: {alpha_float} ====")
            
            if alpha_float > staked_float + default_delta_price:
                if staked:
                    unstaked = unstake_from_subnet(netuid, subtensor, wallet, hotkey)
                    if unstaked:
                        # staked_price = exchange_rates(netuid, subtensor)
                        # staked_float = float(str(staked_price).replace('τ', ''))
                        staked = False
                        get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
                        time.sleep(60)
                    else:
                        print("Failed to unstake")
                else:
                    pass
            elif alpha_float == staked_float:
                print("No change in price")
            elif alpha_float < staked_float - default_delta_price:
                if not staked:
                    staked = stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
                    if staked:
                        # staked_price = exchange_rates(netuid, subtensor)
                        # staked_float = float(str(staked_price).replace('τ', ''))
                        get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
                        time.sleep(60)
                    else:
                        print("Failed to stake")
                else:
                    # print("Already staked")
                    pass

            subtensor.wait_for_block()
            time.sleep(60)
        except Exception as e:
            time.sleep(30)
            print(f"=== Unexpected Error: {e} ===")

if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    hotkey = input("Enter the hotkey: ")
    user_stake_amount = float(input("Enter the stake amount: "))
    
    subtensor = bt.subtensor('local')
    alpha_to_tao = exchange_rates(netuid, subtensor)
    alpha_float = float(str(alpha_to_tao).replace('τ', ''))
    print(f"Alpha to tao: {alpha_float}")
    
    entry_price = float(input("Enter the entry price: "))

    # Create a wallet instance
    wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
    wallet.unlock_coldkey()
    
    cheat1(netuid, subtensor, wallet, sn_vali_addr(netuid), user_stake_amount, entry_price)