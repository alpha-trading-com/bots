import time
import bittensor as bt
from utils.const import sn_vali_addr
from utils.utils import *

        
if __name__ == '__main__':
    
    netuid = int(input("Enter the netuid: "))

    subtensor = bt.subtensor('local')
    subnet = subtensor.subnet(netuid=netuid)
    alpha_price = subnet.alpha_to_tao(1)
    print(f"Current alpha token price: {alpha_price} TAO")

    wallet_name = input("Enter the wallet name: ")            
    wallet = bt.wallet(name=wallet_name)
    wallet.unlock_coldkey()
    #pool_address = '5H1hpYcpLgCYLthKwEnmWzjWMVxvmrv1UckZRxfVFHZkkZzv'
    dest_hotkey = "5FKz1PAcB1y5vn3aGqNog2vyxagrKMjbkMRpdjY9cuXAG6pD"

    print("Press Ctrl+C to stop the script")
    
    while True:
        try:
            alpha_price = subnet.alpha_to_tao(1)
            logger.info(f"Current alpha token price: {alpha_price} TAO")
            
            meta = subtensor.metagraph(netuid)
            hotkeys = meta.hotkeys
            
            for hotkey_addr in hotkeys:
                if hotkey_addr == dest_hotkey:
                    continue
                
                stake = subtensor.get_stake(
                    coldkey_ss58=wallet.coldkeypub.ss58_address,
                    hotkey_ss58=hotkey_addr,
                    netuid=netuid
                )
                if stake > 0:
                    logger.info(f"Found stake of {stake} TAO for hotkey {hotkey_addr}")
                    result = subtensor.move_stake(
                        wallet=wallet,
                        origin_hotkey=hotkey_addr,
                        origin_netuid=netuid,
                        destination_hotkey=dest_hotkey,
                        destination_netuid=netuid,
                        amount=stake
                    )
                    logger.info(f"result: {result}")
                    # Wait a block between unstakes
                    subtensor.wait_for_block()
            
            # deregged_hotkeys = [
            #     '5EhoryScqfDmbzXnpHhdv3rN68yZJvZxQjjeEJgicy9qqCgc',
            #     '5FCxQ1kv4q3tgiTMUH7845wDsGho9oGSrmKevpYuRDnWgpgD',
            #     '5HH2XtfGxEw8yVeynPFEuVJg2rZPpjBHZY5ubKtUdUzyk85x',
            #     '5FqXgm3se8BbXnZrD1eRTng5yJbvbZ7EAif34c3Dr2BMb3bV'
            # ]
            # for hotkey_addr in deregged_hotkeys:
            #     stake = subtensor.get_stake(
            #         coldkey_ss58=wallet.coldkeypub.ss58_address,
            #         hotkey_ss58=hotkey_addr,
            #         netuid=netuid
            #     )
            #     if stake > 0:
            #         logger.info(f"Found stake of {stake} TAO for hotkey {hotkey_addr}")
            #         result = subtensor.move_stake(
            #             wallet=wallet,
            #             origin_hotkey=hotkey_addr,
            #             origin_netuid=netuid,
            #             destination_hotkey=dest_hotkey,
            #             destination_netuid=netuid,
            #             amount=stake
            #         )
            #         logger.info(f"result: {result}")
            #         # Wait a block between unstakes
            #         subtensor.wait_for_block()
            # print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
        
