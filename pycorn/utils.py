import bittensor as bt

def stake_to_subnet(
    subtensor, 
    netuid, 
    wallet, 
    dest_hotkey, 
    tao_amount, 
    min_tolerance_staking = True, 
    rate_tolerance = 0.005, 
    retries = 1
):
    subnet = subtensor.subnet(netuid=netuid)
    min_tolerance = tao_amount / subnet.tao_in.tao

    if min_tolerance_staking:
        rate_tolerance = min_tolerance + 0.005

    for _ in range(retries):
        try:
            result = subtensor.add_stake(
                netuid=netuid,
                amount= bt.Balance.from_tao(tao_amount, netuid),
                wallet=wallet,
                hotkey_ss58=dest_hotkey,
                safe_staking=True,
                rate_tolerance=rate_tolerance
            )
            if result:
                return True
        except Exception as e:
            continue

    return False
