import time
import bittensor as bt
from utils.const import sn_vali_addr
from utils.utils import *

default_delta_price = 0.0001
hotkey54 = "5CPR71gqPyvBT449xpezgZiLpxFaabXNLmnfcQdDw2t3BwqC"
# stake_amount = 1
def get_alpha_to_tao(netuid, subtensor):
    try:
        alpha_to_tao = exchange_rates(netuid, subtensor)
        if isinstance(alpha_to_tao, dict):
            alpha_float = float(alpha_to_tao.get('rate', 0))
        else:
            alpha_float = float(str(alpha_to_tao).replace('τ', '').strip())
        return alpha_float
    except Exception as e:
        logger.error(f"Error getting exchange rate: {e}")
        return 0

def cheat1(netuid, subtensor, wallet, hotkey, entry_price):
    
    alpha_float = get_alpha_to_tao(netuid, subtensor)
    logger.info(f"Alpha to tao: {alpha_float}")
    
    staked = False
    
    amount = subtensor.get_stake(
        coldkey_ss58=wallet.coldkeypub.ss58_address,
        hotkey_ss58=hotkey54,
        netuid=54
    )
    stake = convert_rao_to_tao(amount)
    if alpha_float < entry_price:
        if stake > 0:
            staked = move_stake(54, subtensor, wallet, hotkey54, stake, hotkey, netuid)
            staked_float = get_alpha_to_tao(netuid, subtensor)
            logger.info(f'transfer alpha {stake} from 54 to {netuid}. Result: {staked}')
            subtensor.wait_for_block()
            time.sleep(60)
    else:
        staked_float = entry_price
        logger.info("Alpha to tao is too high, skipping stake")
        time.sleep(60)
        
    while True:
        try:
            alpha_float = get_alpha_to_tao(netuid, subtensor)
            logger.info(f"[{netuid} staked: {staked} amount: {stake}] ===> Staked price: {staked_float} || Alpha to tao: {alpha_float} ====")
            
            if alpha_float > staked_float + default_delta_price:
                if staked:
                    amount = subtensor.get_stake(
                        coldkey_ss58=wallet.coldkeypub.ss58_address,
                        hotkey_ss58=hotkey54,
                        netuid=54
                    )
                    stake = convert_rao_to_tao(amount)
                    unstaked = move_stake(netuid, subtensor, wallet, hotkey, stake, hotkey54, 54)
                    if unstaked:
                        staked_float = get_alpha_to_tao(netuid, subtensor)
                        staked = False
                        time.sleep(60)
                    else:
                        logger.error("Failed to unstake")
            elif alpha_float == staked_float:
                logger.info("No change in price")
            elif alpha_float < staked_float - default_delta_price:
                if not staked:
                    amount = subtensor.get_stake(
                        coldkey_ss58=wallet.coldkeypub.ss58_address,
                        hotkey_ss58=hotkey54,
                        netuid=54
                    )
                    stake = convert_rao_to_tao(amount)
                    staked = move_stake(54, subtensor, wallet, hotkey54, stake, hotkey, netuid)
                    if staked:
                        staked_float = get_alpha_to_tao(netuid, subtensor)
                        time.sleep(60)
                    else:
                        logger.error("Failed to stake")

            subtensor.wait_for_block()
            time.sleep(60)
        except Exception as e:
            time.sleep(90)
            logger.error(f"=== Unexpected Error: {e} ===")

if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    hotkey = input("Enter the hotkey: ")
    
    subtensor = bt.subtensor('finney')
    alpha_float = get_alpha_to_tao(netuid, subtensor)

    logger.info(f"Alpha to tao: {alpha_float}")
    
    entry_price = float(input("Enter the entry price: "))

    # Create a wallet instance
    wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
    wallet.unlock_coldkey()
    
    cheat1(netuid, subtensor, wallet, sn_vali_addr(netuid), entry_price)