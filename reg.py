import bittensor as bt
from pycorn.revised_registration import dtao_register

if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    hotkey = input("Enter the hotkey: ")

    # Create a wallet instance
    wallet = bt.wallet(name=wallet_name, hotkey=hotkey)
    wallet.unlock_coldkey()
    
    subtensor = bt.subtensor('local')
    meta = subtensor.metagraph(netuid)
    block = meta.last_step + meta.tempo
    prev_adjustment_block = subtensor.query_map_subtensor(name='LastAdjustmentBlock',params=(),block=subtensor.block)[netuid][1].value
    block = prev_adjustment_block + 360

    print(f"Registering to the subnet {netuid} at block {block}")
    dtao_register(netuid, subtensor, wallet, block)