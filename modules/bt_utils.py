import bittensor as bt

total_value_dict = {}

def get_owner_coldkeys():
    subtensor = bt.subtensor("finney")
    subnet_infos = subtensor.all_subnets()
    return [subnet_info.owner_coldkey for subnet_info in subnet_infos]

def get_stake_list(subtensor, wallet_ss58):
    if wallet_ss58 in total_value_dict:
        return total_value_dict[wallet_ss58]

    stake_infos = subtensor.get_stake_for_coldkey(
        coldkey_ss58=wallet_ss58
    )
    subnet_infos = subtensor.all_subnets()
    # stake_infos is a list of StakeInfo objects
    balance = subtensor.get_balance(wallet_ss58)
    total_value = balance
    for info in stake_infos:
        subnet_info = subnet_infos[info.netuid]
        value = subnet_info.price.tao * info.stake.tao
        total_value += value

    total_value_dict[wallet_ss58] = total_value
    
    return total_value


