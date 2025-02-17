import time
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
    # print("alpha_to_tao_with_slippage", subnet.alpha_to_tao_with_slippage(1))
    # print(
    #     "alpha_to_tao_with_slippage percentage",
    #     subnet.alpha_to_tao_with_slippage(1, percentage=True),
    # )

    # print("tao_to_alpha_with_slippage", subnet.tao_to_alpha_with_slippage(1))
    # print(
    #     "tao_to_alpha_with_slippage percentage",
    #     subnet.tao_to_alpha_with_slippage(1, percentage=True),
    # )

    # print("tao_to_alpha", subnet.tao_to_alpha(1))
    # print("alpha_to_tao", subnet.alpha_to_tao(1))
    
    return subnet.alpha_to_tao(1)

def watching_price(netuid, subtensor):
  while True:
    try:
      print(exchange_rates(netuid, subtensor))
      time.sleep(12)
    except Exception as e:
      print(e)
      continue

def get_balance_coldkey(subtensor, address):
    balance = subtensor.get_balance(address)
    print(f"==== Balance of {address}: {balance} ====")
    return balance

def stake_to_subnet(netuid, subtensor, wallet, hotkey, tao_amount):
    try:
        subnet = subtensor.subnet(netuid=netuid)
        amount = bt.Balance.from_tao(tao_amount)
        
        stake = subtensor.add_stake(
            netuid=netuid,
            amount=amount,
            wallet=wallet,
            hotkey_ss58=hotkey
        )
        
        current_stake = subtensor.get_stake(
            coldkey_ss58 = wallet.coldkeypub.ss58_address,
            hotkey_ss58 = hotkey,
            netuid = netuid,
        )
        print (f'=== staked netuid {netuid} price {subnet.price} stake {current_stake} ===')
        print(f"=== staked {amount} TAO to {hotkey} on {netuid} ===\n")
        return True
    except Exception as e:
        print(f"Error staking to subnet {netuid}: {e}")
        return False

def calc_tao_amount(netuid, subtensor, wallet, hotkey):
    subnet = subtensor.subnet(netuid=netuid)
    return subnet.price

def unstake_from_subnet(netuid, subtensor, wallet, hotkey, tao_amount):
    try:
        subnet = subtensor.subnet(netuid=netuid)
        amount = subnet.tao_to_alpha(tao_amount)
        
        subtensor.unstake(
            netuid=netuid,
            amount=amount,  # Now using the converted Balance amount
            wallet=wallet,
            hotkey_ss58=hotkey
        )
        print(f"==== Unstaked {amount} TAO from {hotkey} on {netuid} ====")
        return True
    except Exception as e:
        print(f"Error unstaking from subnet {netuid}: {e}")
        return False
