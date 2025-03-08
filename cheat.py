import time
import bittensor as bt
from utils.const import sn_vali_addr
from utils.utils import *
import logging
from datetime import datetime

# Setup logging
def setup_logger():
    log_filename = f"cheat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()
default_delta_price = 0.0005
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

def cheat1(netuid, subtensor, wallet, hotkey, tao_amount, entry_price):
    get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
    
    alpha_float = get_alpha_to_tao(netuid, subtensor)
    logger.info(f"Alpha to tao: {alpha_float}")
    
    ready_to_unstake = False
    ready_to_stake = False
    
    staked = False
    
    if alpha_float < entry_price:
        staked = stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
        staked_float = get_alpha_to_tao(netuid, subtensor)
        get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
        subtensor.wait_for_block()
        time.sleep(60)
    else:
        staked_float = entry_price
        logger.info("Alpha to tao is too high, skipping stake")
        time.sleep(60)
        
    while True:
        try:
            alpha_float = get_alpha_to_tao(netuid, subtensor)
            logger.info(f"[{netuid} staked: {staked} amount: {tao_amount}] ===> Staked price: {staked_float} || Alpha to tao: {alpha_float} ====")
            
            if alpha_float > staked_float + default_delta_price:
                ready_to_stake = False
                if staked:
                    if ready_to_unstake:
                        unstaked = unstake_from_subnet(netuid, subtensor, wallet, hotkey)
                        if unstaked:
                            ready_to_unstake = False
                            staked_float = get_alpha_to_tao(netuid, subtensor)
                            staked = False
                            get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
                            time.sleep(60)
                        else:
                            logger.error("Failed to unstake")
                    else:
                        ready_to_unstake = False
                else:
                    ready_to_unstake = False
            elif alpha_float == staked_float:
                ready_to_unstake = False
                ready_to_stake = False
                logger.info("No change in price")
            elif alpha_float < staked_float - default_delta_price:
                ready_to_unstake = False
                if not staked:
                    if ready_to_stake:
                        staked = stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount)
                        if staked:
                            staked_float = get_alpha_to_tao(netuid, subtensor)
                            get_balance_coldkey(subtensor, wallet.coldkeypub.ss58_address)
                            ready_to_stake = False
                            time.sleep(60)
                        else:
                            logger.error("Failed to stake")
                    else:
                        ready_to_stake = True
                else:
                    ready_to_stake = False

            subtensor.wait_for_block()
            time.sleep(60)
        except Exception as e:
            time.sleep(30)
            logger.error(f"=== Unexpected Error: {e} ===")

if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    hotkey = input("Enter the hotkey: ")
    user_stake_amount = float(input("Enter the stake amount: "))
    
    subtensor = bt.subtensor('local')
    alpha_float = get_alpha_to_tao(netuid, subtensor)

    logger.info(f"Alpha to tao: {alpha_float}")
    
    entry_price = float(input("Enter the entry price: "))

    # Create a wallet instance
    wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
    wallet.unlock_coldkey()
    
    cheat1(netuid, subtensor, wallet, sn_vali_addr(netuid), user_stake_amount, entry_price)