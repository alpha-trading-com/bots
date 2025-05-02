import bittensor as bt
from pycorn.revised_registration import dtao_register

if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    hotkey = input("Enter the hotkey: ")
    delta_block = int(input("Enter the delta block: "))

    # Create a wallet instance
    wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
    wallet.unlock_coldkey()
    
    subtensor = bt.subtensor('finney')
    prev_adjustment_block = subtensor.query_map_subtensor(name='LastAdjustmentBlock',params=(),block=subtensor.block)[netuid][1].value
    block = prev_adjustment_block + 360
    
    if delta_block == -100:
        block = 0
    else:
        block = block + delta_block

    print(f"Registering to the subnet {netuid} at block {block}")
    dtao_register(netuid, subtensor, wallet, block)