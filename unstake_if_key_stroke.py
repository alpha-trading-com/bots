import time
import bittensor as bt
from utils.const import sn_vali_addr
from utils.utils import *

        
if __name__ == '__main__':
    
    netuid = int(input("Enter the netuid: "))

    subtensor = bt.subtensor('finney')
    subnet = subtensor.subnet(netuid=netuid)
    alpha_price = subnet.alpha_to_tao(1)
    print(f"Current alpha token price: {alpha_price} TAO")

    wallet_name = input("Enter the wallet name: ")            
    wallet = bt.wallet(name=wallet_name)
    wallet.unlock_coldkey()
    round_table_hotkey = '5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v'
    dest_hotkey = input("Enter the destination hotkey (default is Round table): ") or round_table_hotkey
    
    print("Press 'y' to unstake, or Ctrl+C to exit")
    try:
        if input().lower() == 'y':
            while True:
                try:
                    result = subtensor.unstake(
                        netuid=netuid,
                        wallet=wallet,
                        hotkey_ss58=dest_hotkey,
                    )
                    if result:
                        break
                except Exception as e:
                    logger.error(f"Error: {e}")
                    continue
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Error: {e}")
        
