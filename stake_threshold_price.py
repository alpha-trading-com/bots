import time
import bittensor as bt
from utils.const import sn_vali_addr
from utils.utils import *
from constants import NETWORK, ROUND_TABLE_HOTKEY
from pycorn.utils import stake_to_subnet
        
if __name__ == '__main__':
    
    netuid = int(input("Enter the netuid: "))
    threshold = float(input("Enter the threshold price (in TAO): "))

    subtensor = bt.subtensor(network=NETWORK)
    subnet = subtensor.subnet(netuid=netuid)
    alpha_price = subnet.alpha_to_tao(1)
    print(f"Current alpha token price: {alpha_price} TAO")

    wallet_name = input("Enter the wallet name: ")            
    wallet = bt.wallet(name=wallet_name)
    wallet.unlock_coldkey()
    dest_hotkey = input("Enter the destination hotkey (default is Round table): ") or ROUND_TABLE_HOTKEY
    
    print("Press Ctrl+C to stop the script")
    while True:
        try:
            subnet = subtensor.subnet(netuid=netuid)
            alpha_price = subnet.alpha_to_tao(1)
            logger.info(f"Current alpha token price: {alpha_price} TAO")
            
            if threshold != -1 and alpha_price > bt.Balance.from_tao(threshold):
                logger.info(f"Current price {alpha_price} TAO is above threshold {threshold} TAO. Skipping...")
                continue
            
            result = stake_to_subnet(
                subtensor=subtensor,
                netuid=netuid,
                wallet=wallet,
                dest_hotkey=dest_hotkey,
                tao_amount=80,
                min_tolerance_staking=True,
                rate_tolerance=0.005
            )
            if result:
                break
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
        
