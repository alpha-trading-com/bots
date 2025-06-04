import time
import bittensor as bt
from utils.const import sn_vali_addr
from utils.utils import *
from constants import ROUND_TABLE_HOTKEY
        
if __name__ == '__main__':
    
    netuid = int(input("Enter the netuid: "))

    subtensor = bt.subtensor('finney')
    subnet = subtensor.subnet(netuid=netuid)
    alpha_price = subnet.alpha_to_tao(1)
    print(f"Current alpha token price: {alpha_price} TAO")

    wallet_name = input("Enter the wallet name: ")            
    wallet = bt.wallet(name=wallet_name)
    wallet.unlock_coldkey()
    #pool_address = '5H1hpYcpLgCYLthKwEnmWzjWMVxvmrv1UckZRxfVFHZkkZzv'
    dest_hotkey = ROUND_TABLE_HOTKEY

    print("Press Ctrl+C to stop the script")
    
    while True:
        try:
            alpha_price = subnet.alpha_to_tao(1)
            logger.info(f"Current alpha token price: {alpha_price} TAO")
            
            meta = subtensor.metagraph(netuid)
            hotkeys = meta.hotkeys
            
            for hotkey_addr in hotkeys:
                if hotkey_addr == dest_hotkey:
                    continue
                
                stake = subtensor.get_stake(
                    coldkey_ss58=wallet.coldkeypub.ss58_address,
                    hotkey_ss58=hotkey_addr,
                    netuid=netuid
                )
                if stake > 0:
                    logger.info(f"Found stake of {stake} TAO for hotkey {hotkey_addr}")
                    result = subtensor.move_stake(
                        wallet=wallet,
                        origin_hotkey=hotkey_addr,
                        origin_netuid=netuid,
                        destination_hotkey=dest_hotkey,
                        destination_netuid=netuid,
                        amount=stake
                    )
                    logger.info(f"result: {result}")
                    # Wait a block between unstakes
                    subtensor.wait_for_block()
            
            deregged_hotkeys = [
                "5HYpPntNoXLFhp7GedCssWXTTS95Pksxxic8TkUPvLwnpPtR",
                "5HQSAGSWAaPZZ6Yxxgg3GQm5Dm6EzPjPd7BtFpkWBwq4ToL1",
                "5C7ZKkwDTSf89pKGTbD8BjqvwyaWyN8qZY38wWQxybQMFcjp",
                "5DXD5qbizv5Nct44VwrEYvRvzLRNNjurw2XgM4DtR2kC1FLF",
                "5D2MwaGVq8Zm6UsnmLGM8yg4tybzbwUtjsfNLJfDdXrRbNq1",
                "5FWq3nMw1MPDx2i4n4bKd4bugjmLPLtYsbBKnU73VeCstCdx",
                "5G6MYC2iZdqA6atwjVAgw3nyjvmXygJ4GEib9qox2MfWANWc",
                "5CyZQs1xHzLuvutoeAkh486faH78cZtE3hmiukAcgtMTHsdD",
                "5DLrM2hpH6v1qu3GHMFFTD1Vh3jRCJiEeG6WxQD61nvMzxQe",
                "5EPcWMLcGkcpAsGpiGvFnTZMWvVpZs6dNcDGiKqxWb6ZCaSR",
                "5EFWKHmtKc2brG4mvywT2PpbZmVskcMHXHZtjR8A5s4Lftmd",
                "5EedHwQSYZLAtUUmQk6R2d8Hyh3Msn5ZzVdQCJWWU6ZcZXTB",
                "5GgPowZon5VivBa7Gu9LVjYUAtQS7ngxSbGboADDrBuw6uuC",
                "5HDtQiPjdCPhM8zh5Jv6bfKLJNu3mESXJBGaebEzYF3NRmyu",
                "5HC7FMzgpy529kRP9LP2VDwCbJmDQQKRyfUkUDbgjLL3vHkN",
                "5GGymrP2X64ko3nxLEP4iR3g8rgrQQzeiL4e6VNWiKXgcciZ",
                "5EveXqcAc85GzXWiXnmnDstd4Hx5Kpo8Hw58BPGQqpU7dFnq",
                "5FCxQ1kv4q3tgiTMUH7845wDsGho9oGSrmKevpYuRDnWgpgD",
                "5D5ZErASWQcbRSPi3pNhEkaDneAcT2A2gFMAzmrt7kCpEGSp",
                "5HgWcERinNgH8nV2VB22rt6mKsdhT4atzgs7sbxBoHZacZ4n",
                "5D1uVctXmAKwippo4fxssKRhypE6UDG26cwXguHDqxCBEu97",
                "5FQo1QKJWccAD9UbuACbaR3odkBubdMkaeny4Wfwnmq1bP8v",
                "5CAyb5bHy7X22sXwPXVDATErYYjTgEbmaGv5YcxL9nYPZUmb",
                "5EZ2NNBAjEkcuoDaxoH7N59YwTWZiHy6JiuCkMZHG3WDEKQv",
                "5EhM2GSQXUPV9Je8X4NKz2VGUhV2kzNDPcfb1qfF4PYvzNuE",
                "5ECW6RuP491ZMehBLg58KyhQL17Srz5yrqBR75BVD5dYV25K",
            ]
            for hotkey_addr in deregged_hotkeys:
                stake = subtensor.get_stake(
                    coldkey_ss58=wallet.coldkeypub.ss58_address,
                    hotkey_ss58=hotkey_addr,
                    netuid=netuid
                )
                if stake > 0:
                    logger.info(f"Found stake of {stake} TAO for hotkey {hotkey_addr}")
                    result = subtensor.move_stake(
                        wallet=wallet,
                        origin_hotkey=hotkey_addr,
                        origin_netuid=netuid,
                        destination_hotkey=dest_hotkey,
                        destination_netuid=netuid,
                        amount=stake
                    )
                    logger.info(f"result: {result}")
                    # Wait a block between unstakes
                    subtensor.wait_for_block()
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
        
