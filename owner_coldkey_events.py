import bittensor as bt
import threading
import requests
import re
import json
import time

NETWORK = "finney"
#NETWORK = "ws://161.97.128.68:9944"
subtensor = bt.subtensor(NETWORK)



WEBHOOK_URL = "https://discord.com/api/webhooks/1396875737952292936/Bggfi9QEHVljmOxaqzJniLwQ70oCjnlj0lb7nIBq4avsVya_dkGNfjOKaGlOt_urwdul"
WEBHOOK_URL_OWN = "https://canary.discord.com/api/webhooks/1410255303689375856/Rkt1TkqmxV3tV_82xFNz_SRP7O0RVBVPaOuZM4JXveyLYypFKqi05EeSCKc4m1a9gJh0"
WEBHOOK_URL_AETH = "https://discord.com/api/webhooks/1420813134410682378/KXZ6CZeoPDr-h_balb62sZA_xnVtUsAyaNU1udShLzJfW7chTUwzd83IxfPS_1XaUBS0"
WEBHOOK_URL_WALLET_TRANSACTIONS = "https://discord.com/api/webhooks/1443556449165901864/Y80Cyvwlzr_Zb5iL1t1H7KPOnQUwYKt8TPho5XhjAbZXaoMIhqXW-LXV9OlxcL_a6ZOa"
WEBHOOK_URL_MINI_WALLET_TRANSACTIONS = "https://discord.com/api/webhooks/1443556723133775902/zC_O25YvNxsMXrnRGEMQWe_vPypeA2LUg72X_vKcUchLy5FjtQbxDCwWikqBJWrD49fe"
WEBHOOK_URL_TRANSFER_TRANSACTIONS = "https://discord.com/api/webhooks/1445165442925723660/rpQjJaewW0ZPTHs2KyHD1ClsXr0BDcmMcm1V9jviuwHcjP4TXVD9FU3Pg3ncNPMHwFXl"

NETWORK = "finney"
#NETWORK = "ws://34.30.248.57:9944"

class DiscordBot:
    def __init__(self):
        self.webhook_url = WEBHOOK_URL

    def send_message(self, content):
        #self.send_message_ours(content)
        self.send_message_to_aeth(content)

    def send_message_ours(self, content):
        data = {
            "content": content,
            "username": "Coldkey Swap Bot",  # Optional: Custom username for the webhook
            "avatar_url": "https://vidaio-justin.s3.us-east-2.amazonaws.com/favicon.ico"  # Optional: Custom avatar for the webhook
        }
        response = requests.post(self.webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        if response.status_code == 204:
            print("Message sent successfully!")
            return True
        else:
            print(f"Failed to send message: {response.status_code}, {response.text}")
        return False

    def send_message_to_aeth(self, content):
        data = {
            "content": content,
            "username": "Aeth Bot",  # Optional: Custom username for the webhook
            "avatar_url": "https://vidaio-justin.s3.us-east-2.amazonaws.com/favicon.ico"  # Optional: Custom avatar for the webhook
        }
        response = requests.post(WEBHOOK_URL_AETH, data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        if response.status_code == 204:
            print("Message sent successfully!")
            return True
        else:
            print(f"Failed to send message: {response.status_code}, {response.text}")
        return False

    def send_message_to_my_own(self, content):
        data = {
            "content": content,
            "username": "Coldkey Swap Bot",  # Optional: Custom username for the webhook
            "avatar_url": "https://vidaio-justin.s3.us-east-2.amazonaws.com/favicon.ico"  # Optional: Custom avatar for the webhook
        }
        response = requests.post(WEBHOOK_URL_OWN, data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        if response.status_code == 204:
            print("Message sent successfully!")
            return True
        else:
            print(f"Failed to send message: {response.status_code}, {response.text}")
        return False

    def send_message_to_wallet_transactions(self, content):
        data = {
            "content": content,
            "username": "Wallet Transactions",  # Optional: Custom username for the webhook
            "avatar_url": "https://vidaio-justin.s3.us-east-2.amazonaws.com/favicon.ico"  # Optional: Custom avatar for the webhook
        }
        response = requests.post(WEBHOOK_URL_WALLET_TRANSACTIONS, data=json.dumps(data), headers={"Content-Type": "application/json"})

        if response.status_code == 204:
            print("Message sent successfully!")
            return True
        else:
            print(f"Failed to send message: {response.status_code}, {response.text}")
        return False

    def send_message_to_mini_wallet_transactions(self, content):

        data = {
            "content": content,
            "username": "Mini Wallet Transactions",  # Optional: Custom username for the webhook
            "avatar_url": "https://vidaio-justin.s3.us-east-2.amazonaws.com/favicon.ico"  # Optional: Custom avatar for the webhook
        }
        response = requests.post(WEBHOOK_URL_MINI_WALLET_TRANSACTIONS, data=json.dumps(data), headers={"Content-Type": "application/json"})


        if response.status_code == 204:
            print("Message sent successfully!")
            return True
        else:
            print(f"Failed to send message: {response.status_code}, {response.text}")
        return False

    def send_message_to_transfer_transactions(self, content):
        data = {
            "content": content,
            "username": "Transfer Transactions",  # Optional: Custom username for the webhook
            "avatar_url": "https://vidaio-justin.s3.us-east-2.amazonaws.com/favicon.ico"  # Optional: Custom avatar for the webhook
        }
        response = requests.post(WEBHOOK_URL_TRANSFER_TRANSACTIONS, data=json.dumps(data), headers={"Content-Type": "application/json"})

        if response.status_code == 204:
            print("Message sent successfully!")
            return True
        else:
            print(f"Failed to send message: {response.status_code}, {response.text}")
        return False

discord_bot = DiscordBot()

def get_owner_coldkeys():
    subtensor = bt.subtensor("finney")
    subnet_infos = subtensor.all_subnets()
    return [subnet_info.owner_coldkey for subnet_info in subnet_infos]

def refresh_owner_coldkeys_periodically(interval_minutes=20):
    global owner_coldkeys
    owner_coldkeys = get_owner_coldkeys()
    threading.Timer(interval_minutes * 60, refresh_owner_coldkeys_periodically, [interval_minutes]).start()

refresh_owner_coldkeys_periodically()



def load_wallet_owners_from_gdoc():
    url = "https://docs.google.com/document/d/167NEkUZkpzZx1L-jDgjdDQNhu5rlddpV__rArvTfqoo/export?format=txt"
    try:
        global wallet_owners, mini_wallet_owners
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        text = response.text
        # Each pair is like: <wallet_address> <owner_name>
        # build a dict mapping wallet address to owner name
        wallet_owners = {}
        mini_wallet_owners = {}
        pattern = r'(5[1-9A-HJ-NP-Za-km-z]{47})\s+([^\s]+)'
        for match in re.findall(pattern, text):
            address, owner = match
            # INSERT_YOUR_CODE
            if owner.startswith("big_"):
                wallet_owners[address] = owner
            else:
                mini_wallet_owners[address] = owner
    except Exception as e:
        print(f"Failed to load wallet owners from Google Doc: {e}")


load_wallet_owners_from_gdoc()
print(wallet_owners)
print(mini_wallet_owners)

def extract_stake_events_from_data(events_data):
    """
    Extract stake and unstake events from blockchain event data.
    
    Args:
        events_data: List of event dictionaries from blockchain
    
    Returns:
        List of dictionaries containing stake/unstake event information
    """
    stake_events = []
    
    for event in events_data:
        phase = event.get('phase', {})
        event_info = event.get('event', {})
        
        # Check if this is a SubtensorModule event
        if event_info.get('module_id') == 'SubtensorModule':
            event_id = event_info.get('event_id')
            attributes = event_info.get('attributes', {})
            
            # Convert coldkey and hotkey to ss58 addresses if possible
            def to_ss58(addr_bytes, ss58_format = 42):
                if addr_bytes is None:
                    return None
                try:
                    # If it's already a string (SS58 address), return it
                    if isinstance(addr_bytes, str):
                        return addr_bytes
                    pubkey_bytes = bytes(addr_bytes).hex()
                    if not pubkey_bytes.startswith("0x"):
                        pubkey_bytes = "0x" + pubkey_bytes
                    return subtensor.substrate.ss58_encode(pubkey_bytes, ss58_format=ss58_format)
                except Exception as e:
                    print(f"Warning: Failed to encode address: {e}, addr_bytes type: {type(addr_bytes)}")
                    return None
                
            if event_id == 'StakeAdded':
                # The attributes for StakeAdded are a tuple, not a dict.
                # Example: (
                #   ((coldkey_bytes,), (hotkey_bytes,), amount, stake, netuid, block_number)
                # )
                # So we need to unpack the tuple accordingly.
                if isinstance(attributes, tuple) and len(attributes) >= 6:
                    coldkey_tuple = to_ss58(attributes[0][0]) if isinstance(attributes[0], tuple) and len(attributes[0]) > 0 else attributes[0]
                    hotkey_tuple = to_ss58(attributes[1][0]) if isinstance(attributes[1], tuple) and len(attributes[1]) > 0 else attributes[1]
                    amount = attributes[2]
                    # attributes[3] is stake, but we use amount for TAO
                    netuid = attributes[4]
                else:
                    coldkey_tuple = None
                    hotkey_tuple = None
                    amount = None
                    netuid = None
                stake_events.append({
                    'type': 'StakeAdded',
                    'coldkey': coldkey_tuple,
                    'hotkey': hotkey_tuple,
                    'netuid': netuid,
                    'amount': amount,
                    'amount_tao': amount / 1e9 if amount else 0,
                })
                
            elif event_id == 'StakeRemoved':
                # Extract unstake information - also a tuple
                if isinstance(attributes, tuple) and len(attributes) >= 6:
                    coldkey_tuple = to_ss58(attributes[0][0]) if isinstance(attributes[0], tuple) and len(attributes[0]) > 0 else attributes[0]
                    hotkey_tuple = to_ss58(attributes[1][0]) if isinstance(attributes[1], tuple) and len(attributes[1]) > 0 else attributes[1]
                    amount = attributes[2]
                    netuid = attributes[4]
                else:
                    coldkey_tuple = None
                    hotkey_tuple = None
                    amount = None
                    netuid = None
                    block_number = None

                stake_events.append({
                    'type': 'StakeRemoved',
                    'coldkey': coldkey_tuple,
                    'hotkey': hotkey_tuple,
                    'netuid': netuid,
                    'amount': amount,
                    'amount_tao': amount / 1e9 if amount else 0,
                })
                
            elif event_id == 'StakeMoved':
                # Extract stake move information - also a tuple
                if isinstance(attributes, tuple) and len(attributes) >= 6:
                    coldkey_tuple = to_ss58(attributes[0][0]) if isinstance(attributes[0], tuple) and len(attributes[0]) > 0 else attributes[0]
                    from_hotkey_tuple = to_ss58(attributes[1][0]) if isinstance(attributes[1], tuple) and len(attributes[1]) > 0 else attributes[1]
                    to_hotkey_tuple = to_ss58(attributes[3][0]) if isinstance(attributes[3], tuple) and len(attributes[3]) > 0 else attributes[3]
                    netuid = attributes[4]
                    amount = attributes[5]
                else:
                    coldkey_tuple = None
                    from_hotkey_tuple = None
                    to_hotkey_tuple = None
                    netuid = None
                    amount = None
                
                stake_events.append({
                    'type': 'StakeMoved',
                    'coldkey': coldkey_tuple,
                    'from_hotkey': from_hotkey_tuple,
                    'to_hotkey': to_hotkey_tuple,
                    'netuid': netuid,
                    'amount': amount,
                    'amount_tao': amount / 1e9 if amount else 0,
                })
    
    return stake_events


def extract_transfer_events_from_data(events_data):
    # Extract events which transfer TAO, like StakeAdded, StakeRemoved, StakeMoved, and direct TAO transfers
    transfer_events = []
    for event in events_data:
        event_info = event.get('event', {})
        module_id = event_info.get('module_id')
        event_id = event_info.get('event_id')
        attributes = event_info.get('attributes', {})

        # SubtensorMo

        # Balances pallet (native TAO transfers)
        if module_id == 'Balances' and event_id in ('Transfer', 'Deposit'):
            # Transfer between accounts
            if event_id == 'Transfer':
                from_addr = attributes.get('from')
                to_addr = attributes.get('to')
                amount = attributes.get('amount')
                transfer_events.append({
                    'type': 'Transfer',
                    'from': from_addr,
                    'to': to_addr,
                    'amount': amount,
                    'amount_tao': amount / 1e9 if amount else 0,
                })
            # # Deposit event - typically corresponds to fee refund or reward
            # elif event_id == 'Deposit':
            #     to_addr = attributes.get('who')
            #     amount = attributes.get('amount')
            #     transfer_events.append({
            #         'type': 'Deposit',
            #         'to': to_addr,
            #         'amount': amount,
            #         'amount_tao': amount / 1e9 if amount else 0,
            #     })

    return transfer_events

def send_owner_coldkey_message(stake_events):
    message = "Hey @everyone! \n"

    for event in stake_events:
        coldkey = event['coldkey']
        tao_amount = round(float(event['amount_tao']), 2)
        netuid_val = int(event['netuid'])
        
        if coldkey not in owner_coldkeys:
            continue

        if event['type'] == 'StakeAdded':
            color = "🟢"
        elif event['type'] == 'StakeRemoved':
            color = "🔴"
        else:
            continue
        message += (
            f"**Owner {owner_coldkeys.index(coldkey)}**:"
            f"**`{color} {event['type']}`**: {tao_amount} TAO on subnet `#{netuid_val}` from `{coldkey}`\n"
        )

    discord_bot.send_message_to_aeth(message)

def send_famous_wallet_message(stake_events):
    message = "Hey @everyone! \n"
    for event in stake_events:
        coldkey = event['coldkey']
        owner_name = wallet_owners[coldkey][4:]
        tao_amount = round(float(event['amount_tao']), 2)
        netuid_val = int(event['netuid'])
        # Format: Event type bold, owner_name italic, subnet code highlighted
        if event['type'] == 'StakeAdded':
            color = "🟢"
        elif event['type'] == 'StakeRemoved':
            color = "🔴"
        else:
            continue
        message += (
            f"**{owner_name}**:"
            f"**`{color} {event['type']}`**: {tao_amount} TAO on subnet `#{netuid_val}` from `{coldkey}`\n"
        )
    discord_bot.send_message_to_wallet_transactions(message)

def send_mini_wallet_message(stake_events):
    message = "Hey Guys! \n"
    for event in stake_events:
        coldkey = event['coldkey']
        owner_name = mini_wallet_owners[coldkey]
        tao_amount = round(float(event['amount_tao']), 2)
        netuid_val = int(event['netuid'])
        if event['type'] == 'StakeAdded':
            color = "🟢"
        elif event['type'] == 'StakeRemoved':
            color = "🔴"
        else:
            continue
        message += (
            f"**{owner_name}**:"
            f"**`{color} {event['type']}`**: {tao_amount} TAO on subnet `#{netuid_val}` from `{coldkey}`\n"
        )    
    discord_bot.send_message_to_mini_wallet_transactions(message)


def send_message_to_discord(stake_events):
    owner_coldkey_stake_events = []
    famous_wallet_stake_events = []
    mini_wallet_stake_events = []
    for event in stake_events:
        coldkey = event['coldkey']
        if coldkey in owner_coldkeys:
            netuid = owner_coldkeys.index(coldkey)
            if netuid != 20:
                owner_coldkey_stake_events.append(event)
            
        if coldkey in wallet_owners:
            famous_wallet_stake_events.append(event)

        if coldkey in mini_wallet_owners:
            mini_wallet_stake_events.append(event)

    if not owner_coldkey_stake_events and not famous_wallet_stake_events and not mini_wallet_stake_events:
        print("No stake events found")
        return

    if owner_coldkey_stake_events:
        send_owner_coldkey_message(owner_coldkey_stake_events)

    if famous_wallet_stake_events:
        send_famous_wallet_message(famous_wallet_stake_events)

    if mini_wallet_stake_events:
        send_mini_wallet_message(mini_wallet_stake_events)

CEXS = {
    "5FqBL928choLPmeFz5UVAvonBD5k7K2mZSXVC9RkFzLxoy2s": "MEXC",
    "5GBnPzvPghS8AuCoo6bfnK7JUFHuyUhWSFD4woBNsKnPiEUi": "Binance",
}

def send_message_to_discord_transfer(transfer_events):
    message = "Hey @everyone! \n"
    def get_owner_name(addr):
        if addr in owner_coldkeys:
            return f"Owner {owner_coldkeys.index(addr)}"
        elif addr in wallet_owners:
            return f"{wallet_owners[addr]}"
        elif addr in mini_wallet_owners:
            return f"{mini_wallet_owners[addr]}"
        else:
            return "Unknown"

    def get_cexs_name(addr):
        if addr in CEXS:
            return CEXS[addr]
        else:
            return "Unknown"

    exits_message = False
    for event in transfer_events:
        from_addr = event['from']
        to_addr = event['to']
        amount = event['amount']
        amount_tao = event['amount_tao']
        from_owner_name = get_owner_name(from_addr)
        to_owner_name = get_owner_name(to_addr)
        if from_owner_name == "Unknown" and to_owner_name == "Unknown":
            continue

        if amount_tao < 0.5:
            continue

        if from_owner_name == to_owner_name:
            continue

        if from_owner_name == "Unknown":
            from_owner_name = get_cexs_name(from_addr)
        
        if to_owner_name == "Unknown":
            to_owner_name = get_cexs_name(to_addr)

        exits_message = True
        message += (f"**{from_owner_name}**({from_addr}) transferred {amount_tao} TAO to **{to_owner_name}**({to_addr})\n")

    if not exits_message:
        return

    discord_bot.send_message_to_transfer_transactions(message)

if __name__ == "__main__":    
    
    while True:
        try:
            block_number = subtensor.get_current_block()
            block_hash = subtensor.substrate.get_block_hash(block_id=block_number)
            events = subtensor.substrate.get_events(block_hash=block_hash)

            
            # Extract stake events from live data
            stake_events = extract_stake_events_from_data(events)
            transfer_events = extract_transfer_events_from_data(events)
            send_message_to_discord(stake_events)
            send_message_to_discord_transfer(transfer_events)
            subtensor.wait_for_block()
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            time.sleep(1)