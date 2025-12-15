import bittensor as bt

def get_owner_coldkeys():
    subtensor = bt.subtensor("finney")
    subnet_infos = subtensor.all_subnets()
    return [subnet_info.owner_coldkey for subnet_info in subnet_infos]

def get_balance_and_stake_infos(subtensor, wallet_ss58, cache):
    if wallet_ss58 in cache:
        balance, stake_infos = cache[wallet_ss58]
    stake_infos = subtensor.get_stake_for_coldkey(
        coldkey_ss58=wallet_ss58
    )
    # stake_infos is a list of StakeInfo objects
    balance = subtensor.get_balance(wallet_ss58)

    cache[wallet_ss58] = balance, stake_infos
    return cache[wallet_ss58]

def get_total_value(subtensor, wallet_ss58, subnet_infos, current_netuid, cache):
    balance, stake_infos = get_balance_and_stake_infos(subtensor, wallet_ss58, cache)
    free_value = balance.tao
    now_subnet_stake_value = 0
    other_subnet_staked_value = 0

    for info in stake_infos:
        subnet_info = subnet_infos[info.netuid]
        value = subnet_info.price.tao * info.stake.tao
        if info.netuid == 0:
            free_value += value
        elif current_netuid == info.netuid:
            now_subnet_stake_value += value
        else:
            other_subnet_staked_value += value
    
    total_value = free_value + now_subnet_stake_value + other_subnet_staked_value

    # ANSI color codes
    reset = "\033[0m"
    total_color = "\033[96m"  # Bright cyan for total
    free_color = "\033[92m"   # Green for free
    current_color = "\033[94m"  # Blue for current subnet
    other_color = "\033[93m"  # Yellow for other subnets
    
    # Format value: show "---" if value < 0.5, otherwise show formatted float
    def format_value(value):
        if value < 0.5:
            return "---"
        return f"τ{value:.2f}"
    
    result = (
        f"-> "
        f"{total_color}{format_value(total_value)}{reset} "
        f"({free_color}{format_value(free_value)}{reset} | "
        f"{current_color}{format_value(now_subnet_stake_value)} SN{current_netuid}{reset} | "
        f"{other_color}{format_value(other_subnet_staked_value)}{reset})"
    )


    return result


