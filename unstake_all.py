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
    pool_address = '5H1hpYcpLgCYLthKwEnmWzjWMVxvmrv1UckZRxfVFHZkkZzv'
    
    print("Press Ctrl+C to stop the script")
    while True:
        try:
            alpha_price = subnet.alpha_to_tao(1)
            logger.info(f"Current alpha token price: {alpha_price} TAO")
            
            # Skip if current price is below threshold
            if threshold != -1 and alpha_price < bt.Balance.from_tao(threshold):
                logger.info(f"Current price {alpha_price} TAO is below threshold {threshold} TAO. Skipping...")
                continue
            
            meta = subtensor.metagraph(netuid)
            hotkeys = meta.hotkeys
            
            
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

            validator_hotkeys = [
                '5FKz1PAcB1y5vn3aGqNog2vyxagrKMjbkMRpdjY9cuXAG6pD',
            ]
            for hotkey_addr in validator_hotkeys:
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
            
            # Get the total balance after unstaking
            # balance = subtensor.get_balance(wallet.coldkeypub.ss58_address)
            # if balance > 0:
            #     logger.info(f"Found balance of {balance} TAO, transferring to pool...")
            #     try:
            #         result = subtensor.transfer(
            #             wallet=wallet,
            #             dest=pool_address,
            #             amount=balance
            #         )
            #         logger.info(f"Transferred {balance} TAO to pool {pool_address} || result: {result}")
            #     except Exception as e:
            #         logger.error(f"Failed to transfer balance: {e}")
            
            # # Wait a few blocks before checking again
            # for _ in range(3):
            #     subtensor.wait_for_block()
            break
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
        
