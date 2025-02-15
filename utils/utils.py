import bittensor as bt

def old_register(
    netuid, subtensor, wallet, wait_for_inclusion=True, wait_for_finalization=False
):
    while True:
        try:
            receipt = subtensor._do_burned_register(
                netuid=netuid,
                wallet=wallet,
                wait_for_inclusion=wait_for_inclusion,
                wait_for_finalization=wait_for_finalization,
            )
            print(receipt)
            if receipt[0] == True:
                print(
                    f"Successfully registered wallet {wallet.name} {wallet.hotkey} to subnet {netuid}"
                )
                break
            elif "HotKeyAlreadyRegisteredInSubNet" in receipt[1]:
                print(f"Hotkey {wallet.hotkey} already registered in subnet {netuid}")
                break
        except Exception as e:
            print(e)
            continue

def dtao_register(netuid, subtensor, wallet):
    while True:
        try:
            receipt = subtensor.burned_register(
                netuid=netuid,
                wallet=wallet,
            )
            print(receipt)
            if receipt[0] == True:
                print(f"Successfully registered wallet {wallet.name} {wallet.hotkey} to subnet {netuid}")
                break
            elif "HotKeyAlreadyRegisteredInSubNet" in receipt[1]:
                print(f"Hotkey {wallet.hotkey} already registered in subnet {netuid}")
                break
        except Exception as e:
            print(e)
            continue

def exchange_rates(netuid, subtensor):
    subnet = subtensor.subnet(netuid=netuid)
    print("alpha_to_tao_with_slippage", subnet.alpha_to_tao_with_slippage(1))
    print(
        "alpha_to_tao_with_slippage percentage",
        subnet.alpha_to_tao_with_slippage(1, percentage=True),
    )

    print("tao_to_alpha_with_slippage", subnet.tao_to_alpha_with_slippage(1))
    print(
        "tao_to_alpha_with_slippage percentage",
        subnet.tao_to_alpha_with_slippage(1, percentage=True),
    )

    print("tao_to_alpha", subnet.tao_to_alpha(1))
    print("alpha_to_tao", subnet.alpha_to_tao(1))

def get_balance_coldkey(subtensor, address):
    balance = subtensor.get_balance(address)
    print(balance)
    return balance

def stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount):
    subnet = subtensor.subnet(netuid=netuid)
    stake = subnet.add_stake(
      wallet=wallet,
      netuid=netuid,
      hotkey=hotkey,
      tao_amount = tao_amount
    )
    
    current_stake = subtensor.get_stake(
        coldkey_ss58 = wallet.coldkeypub.ss58_address,
        hotkey_ss58 = hotkey,
        netuid = netuid,
    )
    print(f"=== staked {tao_amount} TAO to {hotkey} on {netuid} ===\n")
    print(current_stake)
    print("=" * 50)


