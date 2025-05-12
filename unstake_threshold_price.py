import time
import bittensor as bt
from utils.const import sn_vali_addr
from utils.utils import *

        
if __name__ == '__main__':
    
    netuid = int(input("Enter the netuid: "))
    threshold = float(input("Enter the threshold price (in TAO): "))

    subtensor = bt.subtensor('finney')
    subnet = subtensor.subnet(netuid=netuid)
    alpha_price = subnet.alpha_to_tao(1)
    print(f"Current alpha token price: {alpha_price} TAO")

    wallet_name = input("Enter the wallet name: ")            
    wallet = bt.wallet(name=wallet_name)
    wallet.unlock_coldkey()
    round_table_hotkey = '5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v'
    dest_hotkey = input("Enter the destination hotkey (default is Round table): ") or round_table_hotkey
    
    print("Press Ctrl+C to stop the script")
    while True:
        try:
            alpha_price = subnet.alpha_to_tao(1)
            logger.info(f"Current alpha token price: {alpha_price} TAO")
            
            if threshold != -1 and alpha_price < bt.Balance.from_tao(threshold):
                logger.info(f"Current price {alpha_price} TAO is below threshold {threshold} TAO. Skipping...")
                continue
            
            unstake_from_subnet(netuid, subtensor, wallet, dest_hotkey)
            break
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
        
