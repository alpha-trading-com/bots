import bittensor as bt
from utils.utils import *

if __name__ == '__main__':
    netuid = int(input("Enter the netuid: "))
    subtensor = bt.subtensor('local')
    
    watching_price(netuid, subtensor)