import bittensor as bt
from constants import NETWORK


def calcuate(t_in, a_in, t_real, t_virtual):
    p = t_in * a_in
    a_virtual = a_in - p / (t_in + t_virtual)
    a_real = a_in - p / (t_in + t_real)

    earning = t_in + t_real - p / (a_in - a_real + a_virtual)
    return earning - t_virtual


def calculate_max_earning(t_in, a_in, t_real):
    max_earning = 0
    max_t_virtual = 0
    for t_virtual in range(1, t_real + 1):
        earning = calcuate(t_in, a_in, t_real, t_virtual)
        if earning > max_earning:
            max_earning = earning
            max_t_virtual = t_virtual
    return max_earning, max_t_virtual


if __name__ == "__main__":
    netuid = 114
    
    subtensor = bt.subtensor(NETWORK)
    initial_fund = 1000
    print(subtensor.get_current_block())
    subnet = subtensor.subnet(netuid)
    t_in = subnet.tao_in.tao
    a_in = subnet.alpha_in.tao

    print(t_in, a_in)
    print(calculate_max_earning(t_in, a_in, 60))