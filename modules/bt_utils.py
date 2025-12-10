import bittensor as bt

def get_owner_coldkeys():
    subtensor = bt.subtensor("finney")
    subnet_infos = subtensor.all_subnets()
    return [subnet_info.owner_coldkey for subnet_info in subnet_infos]