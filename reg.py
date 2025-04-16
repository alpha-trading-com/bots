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
    print(meta.last_step + meta.tempo)
    block = meta.last_step + meta.tempo
    # Register the wallet to the subnet
    dtao_register(netuid, subtensor, wallet, block)