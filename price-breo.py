import bittensor as bt
from utils.utils import *
from constants import NETWORK, NETWORK_FINNEY


if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    subtensor = bt.subtensor(network=NETWORK_FINNEY)
    prev_tao_in = 0
    while True:
        try:
            subnet = subtensor.subnet(netuid=netuid)
            price = subnet.alpha_to_tao(1)
            now_tao_in = subnet.tao_in
            tao_flow = now_tao_in - prev_tao_in
            print(f"{netuid} => {price}, {tao_flow}")
            prev_tao_in = now_tao_in
            subtensor.wait_for_block()
        except Exception as e:
            print(f"Error in watching_price: {e}")
            continue
