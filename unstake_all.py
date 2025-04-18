import time
import bittensor as bt
from utils.const import sn_vali_addr
from utils.utils import *

        
if __name__ == '__main__':
    print("Press Ctrl+C to stop the script")
    while True:
        try:
            netuid = int(input("Enter the netuid: "))
            wallet_name = input("Enter the wallet name: ")
            subtensor = bt.subtensor('finney')
            
            # Create a wallet instance
            wallet = bt.wallet(name=wallet_name)
            wallet.unlock_coldkey()
            
            # Get all neurons in the subnet
            meta = subtensor.metagraph(netuid)
            hotkeys = meta.hotkeys
            
            # Get all stakes for this coldkey
            for hotkey_addr in hotkeys:
                stake = subtensor.get_stake(
                    coldkey_ss58=wallet.coldkeypub.ss58_address,
                    hotkey_ss58=hotkey_addr,
                    netuid=netuid
                )
                if stake > 0:
                    logger.info(f"Found stake of {stake} TAO for hotkey {hotkey_addr}")
                    unstake_from_subnet(netuid, subtensor, wallet, hotkey_addr)
                    # Wait a block between unstakes
                    subtensor.wait_for_block()
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
        
