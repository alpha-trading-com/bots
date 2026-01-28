import bittensor as bt
import requests
import re
import time
import threading

from modules.discord import send_webhook_message
from modules.constants import (
    NETWORK,
    WEBHOOK_URL_AETH_CHAIN_EVENT,
    WEBHOOK_URL_SS_EVENTS,
)


from modules.bt_utils import get_total_value


from modules.constants import (
    GOOGLE_DOC_ID_BOTS,
    GOOGLE_DOC_ID_OWNER_WALLETS,
    GOOGLE_DOC_ID_OWNER_WALLETS_SS,
    GOOGLE_DOC_ID_OWNER_WALLETS_PS,
    NETWORK,
)

REFRESH_INTERVAL = 20 # minutes
subtensor = bt.subtensor(NETWORK)
subtensor_owner_coldkeys = bt.subtensor(NETWORK)

bots = []
wallet_owners = {}
owner_coldkeys = []
wallet_numbers = {}

def load_bots_from_gdoc():
    url = f"https://docs.google.com/document/d/{GOOGLE_DOC_ID_BOTS}/export?format=txt"
    try:
        global bots
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        text = response.text
        bots = re.findall(r'5[1-9A-HJ-NP-Za-km-z]{47}', text)
    except Exception as e:
        print(f"Failed to load bots from Google Doc: {e}")
         
def load_wallet_owners_from_gdoc():
    global wallet_owners
    urls = [
        f"https://docs.google.com/document/d/{GOOGLE_DOC_ID_OWNER_WALLETS}/export?format=txt",
        f"https://docs.google.com/document/d/{GOOGLE_DOC_ID_OWNER_WALLETS_SS}/export?format=txt",
        f"https://docs.google.com/document/d/{GOOGLE_DOC_ID_OWNER_WALLETS_PS}/export?format=txt"
    ]
    for url in urls:    
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            text = response.text
            # Each pair is like: <wallet_address> <owner_name>
            # build a dict mapping wallet address to owner name
            pattern = r'(5[1-9A-HJ-NP-Za-km-z]{47})\s+([^\s]+)'
            for match in re.findall(pattern, text):
                address, owner = match
                wallet_owners[address] = owner

        except Exception as e:
            print(f"Failed to load wallet owners from Google Doc: {e}")

        
def refresh_bots_periodically(interval_minutes=REFRESH_INTERVAL):
    load_wallet_owners_from_gdoc()
    load_bots_from_gdoc()
    threading.Timer(interval_minutes * 60, refresh_bots_periodically, [interval_minutes]).start()

refresh_bots_periodically()


def refresh_owner_coldkeys_periodically(interval_minutes=REFRESH_INTERVAL):
    global owner_coldkeys
    subnet_infos = subtensor_owner_coldkeys.all_subnets()
    owner_coldkeys = [subnet_info.owner_coldkey for subnet_info in subnet_infos]
    threading.Timer(interval_minutes * 60, refresh_owner_coldkeys_periodically, [interval_minutes]).start()

refresh_owner_coldkeys_periodically()

def get_coldkey_display_name(coldkey):
    if coldkey is None:
        return "Unknown"
    owner_color = "\033[93m"
    wallet_number_color = "\033[96m"
    color = "\033[94m"
    reset = "\033[0m" 

    if coldkey in owner_coldkeys:
        return coldkey + f"{owner_color} (owner{owner_coldkeys.index(coldkey)}){reset}"

    if coldkey in bots:
        return coldkey + f"{color} (bot{bots.index(coldkey)+1}){reset}"
    

    if coldkey in wallet_owners:
        return coldkey + f"{owner_color} ({wallet_owners[coldkey]}){reset}"
    
    if coldkey in wallet_numbers:
        wallet_number = wallet_numbers[coldkey]
    else:
        wallet_number = len(wallet_numbers) + 1
        wallet_numbers[coldkey] = wallet_number
    return coldkey + f"{wallet_number_color} (#{wallet_number}){reset}"

def get_color(event_type, coldkey):
    if event_type == 'StakeAdded':
        return "\033[92m"
    elif event_type == 'StakeRemoved':
        return "\033[91m"
    else:
        return "\033[0m"


def extract_stake_extrinsic_from_data(extrinsics, extrinsic_success_map=None):
    """Extract stake extrinsics from the data"""
    stake_extrinsic = []
    
    for idx, ex in enumerate(extrinsics):
        call = ex.value.get('call', {})
        # Fetch add_stake_limit extrinsics and print parsed details
        coldkey = ex.value.get('address', None)
        if (
            call.get('call_module') == 'SubtensorModule' and
            call.get('call_function') == 'add_stake_limit'
        ):
            args = call.get('call_args', [])
            amount_staked = next((a['value'] for a in args if a['name'] == 'amount_staked'), None)
            netuid = next((a['value'] for a in args if a['name'] == 'netuid'), None)
            
            # Check if extrinsic succeeded or failed
            extrinsic_success = extrinsic_success_map.get(idx, None)
            
            stake_extrinsic.append({
                'coldkey': coldkey,
                'type': 'StakeAdded',
                'netuid': netuid,
                'amount_tao': amount_staked/ 1e9,
                'success': extrinsic_success,
            })

        if (
            call.get('call_module') == 'SubtensorModule' and
            call.get('call_function') == 'add_stake'
        ):
            args = call.get('call_args', [])
            amount_staked = next((a['value'] for a in args if a['name'] == 'amount_staked'), None)
            netuid = next((a['value'] for a in args if a['name'] == 'netuid'), None)
            
            # Check if extrinsic succeeded or failed
            extrinsic_success = extrinsic_success_map.get(idx, None)
            
            
            stake_extrinsic.append({
                'coldkey': coldkey,
                'type': 'StakeAdded',
                'netuid': netuid,
                'amount_tao': amount_staked/ 1e9,
                'success': extrinsic_success,
            })

    return stake_extrinsic

def print_stake_extrinsic(stake_extrinsic, threshold, netuid, show_balance):
    now_subnet_infos = subtensor.all_subnets()
    prices = [float(subnet_info.price) for subnet_info in now_subnet_infos]
    cash = {}
    for extrinsic in stake_extrinsic:
        netuid_val = int(extrinsic['netuid'])
        tao_amount = float(extrinsic['amount_tao'])
        if not ((netuid == netuid_val or netuid == -1) and (abs(tao_amount) > threshold or threshold == -1)):
            continue
        
        old_coldkey = extrinsic['coldkey']
        coldkey = get_coldkey_display_name(old_coldkey)

        color = get_color(extrinsic['type'], coldkey)    

        # Green for stake added, red for stake removed (bright)
        if extrinsic['type'] == 'StakeAdded':
            sign = "+"
        elif extrinsic['type'] == 'StakeRemoved':
            sign = "-"
        else:
            continue

        reset = "\033[0m"
        total_value_str = ""
        if show_balance:
            total_value_str = get_total_value(subtensor, old_coldkey, now_subnet_infos, netuid_val, cash)

        # Show green check for success, red cross for failure
        success_str = "✔️" if extrinsic['success'] else "❌"
        if extrinsic['success']:
            continue

        print(f"{color}SN {netuid_val:3d} => {prices[netuid_val]:8.5f}  {sign}{tao_amount:5.1f}  {coldkey}{reset} {total_value_str} {success_str}")

      
if __name__ == "__main__":    

    #netuid = int(input("Enter the netuid: "))
    #threshold = float(input("Enter the threshold: "))
    #show_balance = float(input("Enter whether you want to show wallet balance (yes or no)") == "yes")

    netuid = -1
    threshold = 0.5
    show_balance = True
    
    while True:
        try:
            block_number = subtensor.get_current_block()
            block_hash = subtensor.substrate.get_block_hash(block_id=block_number)
            extrinsics = subtensor.substrate.get_extrinsics(block_hash=block_hash)
            events = subtensor.substrate.get_events(block_hash=block_hash)

            extrinsic_success_map = {}
            for event in events:
                # Extract event module and id as before
                phase = event.get('phase', {})
                event_info = event.get('event', {})
                event_extrinsic_idx = event.get('extrinsic_idx', None)
                if event_info.get('module_id') == "System" and event_info.get('event_id') in ("ExtrinsicSuccess", "ExtrinsicFailed"):
                    if event_info.get('event_id') == "ExtrinsicSuccess":
                        extrinsic_success_map[event_extrinsic_idx] = True
                    elif event_info.get('event_id') == "ExtrinsicFailed":
                        extrinsic_success_map[event_extrinsic_idx] = False
        
            stake_extrinsic = extract_stake_extrinsic_from_data(extrinsics, extrinsic_success_map)
            if stake_extrinsic:
                print(f"*{'*'*40}")
                print_stake_extrinsic(stake_extrinsic, threshold, netuid, show_balance)
            subtensor.wait_for_block()
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)