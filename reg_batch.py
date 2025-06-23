import bittensor as bt
from pycorn.revised_registration import dtao_register
from constants import NETWORK
import time


if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    wallet_name = input("Enter the wallet name: ")
    wallet = bt.wallet(name=wallet_name)
    wallet.unlock_coldkey()

    while True:
        for i in range(1, 20, 1):
            try:
                hotkey = f"hk{i}"
                wallet.set_hotkey(hotkey)
                subtensor = bt.subtensor(network=NETWORK)
                subtensor.burned_register(wallet=wallet, netuid=netuid)
            except Exception as e:
                print(f"Error registering hotkey {hotkey}: {e}")
                continue
