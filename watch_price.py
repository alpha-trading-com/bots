import bittensor as bt
from utils.utils import *
from constants import NETWORK


if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    subtensor = bt.subtensor(network=NETWORK)
    
    watching_price(netuid, subtensor)