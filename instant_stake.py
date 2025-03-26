import time
import bittensor as bt
from utils.const import sn_vali_addr
from utils.utils import *

default_delta_price = 0.00001
stake_amount = 1

def auto_move(netuid, subtensor, wallet, dest_hotkey, tao_amount):
    # unstake_from_subnet(netuid, subtensor, wallet, dest_hotkey)

    # while True:
    try:
        # staked = stake_to_subnet(netuid, subtensor, wallet, dest_hotkey, tao_amount)
        subnet = subtensor.subnet(netuid=netuid)
        amount = bt.Balance.from_tao(tao_amount)
        
        stake = subtensor.add_stake(
            netuid=netuid,
            amount=amount,
            wallet=wallet,
            hotkey_ss58=dest_hotkey
        )

        logger.info(f'=== staked netuid {netuid} price {subnet.price} stake {stake} ===')
        # time.sleep(60)
        current_stake = subtensor.get_stake(
            coldkey_ss58 = wallet.coldkeypub.ss58_address,
            hotkey_ss58 = dest_hotkey,
            netuid = netuid,
        )
        if current_stake:
            result = subtensor.unstake(
                netuid=netuid,
                amount=current_stake,
                wallet=wallet,
                hotkey_ss58=dest_hotkey
            )
            logger.info(f"==== Unstaked {current_stake} TAO from {dest_hotkey} on {netuid} || result: {result} ====")


    except Exception as e:
        logger.error(f"=== Unexpected Error: {e} ===")
        subtensor.wait_for_block()
        time.sleep(60)
            

if __name__ == '__main__':
    # Create a wallet instance
    wallet = bt.wallet(name='taocorn')
    wallet.unlock_coldkey()
    
    subtensor = bt.subtensor('local')
    target_net_uid = 64
    hotkey = "5Fc8ggzwmUMVBWgPjAArTHy6JZS6BJ5q5m7BtqVCSwReDiMQ"
    auto_move(target_net_uid, subtensor, wallet, hotkey, 0.01)
    
