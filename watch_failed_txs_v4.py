import bittensor as bt
import requests
import re
import time
import threading
import hashlib

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


def extract_stake_extrinsic_from_data(extrinsics):
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
            limit_price = next((a['value'] for a in args if a['name'] == 'limit_price'), None)
            netuid = next((a['value'] for a in args if a['name'] == 'netuid'), None)
            hotkey = next((a['value'] for a in args if a['name'] == 'hotkey'), None)
            
            # Convert hotkey to SS58 if it's bytes
            if hotkey is not None:
                try:
                    if not isinstance(hotkey, str):
                        pubkey_bytes = bytes(hotkey).hex()
                        if not pubkey_bytes.startswith("0x"):
                            pubkey_bytes = "0x" + pubkey_bytes
                        hotkey = subtensor.substrate.ss58_encode(pubkey_bytes, ss58_format=42)
                except Exception:
                    pass
            
            stake_extrinsic.append({
                'coldkey': coldkey,
                'hotkey': hotkey,
                'type': 'StakeAdded',
                'netuid': netuid,
                'amount_tao': amount_staked/ 1e9,
                'amount_raw': amount_staked,
                'limit_price': limit_price,
                'extrinsic_idx': idx,
            })

        if (
            call.get('call_module') == 'SubtensorModule' and
            call.get('call_function') == 'add_stake'
        ):
            args = call.get('call_args', [])
            amount_staked = next((a['value'] for a in args if a['name'] == 'amount_staked'), None)
            netuid = next((a['value'] for a in args if a['name'] == 'netuid'), None)
            hotkey = next((a['value'] for a in args if a['name'] == 'hotkey'), None)
            
            # Convert hotkey to SS58 if it's bytes
            if hotkey is not None:
                try:
                    if not isinstance(hotkey, str):
                        pubkey_bytes = bytes(hotkey).hex()
                        if not pubkey_bytes.startswith("0x"):
                            pubkey_bytes = "0x" + pubkey_bytes
                        hotkey = subtensor.substrate.ss58_encode(pubkey_bytes, ss58_format=42)
                except Exception:
                    pass
            
            stake_extrinsic.append({
                'coldkey': coldkey,
                'hotkey': hotkey,
                'type': 'StakeAdded',
                'netuid': netuid,
                'amount_tao': amount_staked/ 1e9,
                'amount_raw': amount_staked,
                'limit_price': 1e9,
                'extrinsic_idx': idx,
            })

        # Check if this is a Proxy.proxy call with nested SubtensorModule call
        if (
            call.get('call_module') == 'Proxy' and
            call.get('call_function') == 'proxy'
        ):
            # Extract the nested call from proxy args
            proxy_args = call.get('call_args', [])
            nested_call = next((a['value'] for a in proxy_args if a['name'] == 'call'), None)
            
            # Extract the Real account (actual coldkey that initiated the proxy)
            real_account = next((a['value'] for a in proxy_args if a['name'] == 'real'), None)
            
            # Handle different proxy call structures
            # Sometimes real is nested in a dict with __kind: 'Id' and Value
            if isinstance(real_account, dict):
                # Try different possible keys
                real_account = (
                    real_account.get('Value') or 
                    real_account.get('value') or
                    real_account.get('Id') or
                    real_account.get('id')
                )
                # If still a dict, try to get the value from nested structure
                if isinstance(real_account, dict):
                    real_account = real_account.get('Value') or real_account.get('value')
            
            # Convert to SS58 if it's bytes
            if real_account is not None and not isinstance(real_account, str):
                try:
                    pubkey_bytes = bytes(real_account).hex()
                    if not pubkey_bytes.startswith("0x"):
                        pubkey_bytes = "0x" + pubkey_bytes
                    real_account = subtensor.substrate.ss58_encode(pubkey_bytes, ss58_format=42)
                except Exception:
                    pass
            
            # Use Real account as coldkey if available, otherwise use proxy address
            actual_coldkey = real_account if real_account else coldkey
            
            # Check if nested call is add_stake_limit
            if (
                nested_call and
                nested_call.get('call_module') == 'SubtensorModule' and
                nested_call.get('call_function') == 'add_stake_limit'
            ):
                args = nested_call.get('call_args', [])
                amount_staked = next((a['value'] for a in args if a['name'] == 'amount_staked'), None)
                netuid = next((a['value'] for a in args if a['name'] == 'netuid'), None)
                hotkey = next((a['value'] for a in args if a['name'] == 'hotkey'), None)
                limit_price = next((a['value'] for a in args if a['name'] == 'limit_price'), None)
                # Convert hotkey to SS58 if it's bytes
                if hotkey is not None:
                    try:
                        if not isinstance(hotkey, str):
                            pubkey_bytes = bytes(hotkey).hex()
                            if not pubkey_bytes.startswith("0x"):
                                pubkey_bytes = "0x" + pubkey_bytes
                            hotkey = subtensor.substrate.ss58_encode(pubkey_bytes, ss58_format=42)
                    except Exception:
                        pass
                
                stake_extrinsic.append({
                    'coldkey': actual_coldkey,
                    'hotkey': hotkey,
                    'type': 'StakeAdded',
                    'netuid': netuid,
                    'amount_tao': amount_staked / 1e9 if amount_staked else 0,
                    'amount_raw': amount_staked,
                    'limit_price': limit_price,
                    'extrinsic_idx': idx,
                })
            
            # Check if nested call is add_stake
            if (
                nested_call and
                nested_call.get('call_module') == 'SubtensorModule' and
                nested_call.get('call_function') == 'add_stake'
            ):
                args = nested_call.get('call_args', [])
                amount_staked = next((a['value'] for a in args if a['name'] == 'amount_staked'), None)
                netuid = next((a['value'] for a in args if a['name'] == 'netuid'), None)
                hotkey = next((a['value'] for a in args if a['name'] == 'hotkey'), None)
                
                # Convert hotkey to SS58 if it's bytes
                if hotkey is not None:
                    try:
                        if not isinstance(hotkey, str):
                            pubkey_bytes = bytes(hotkey).hex()
                            if not pubkey_bytes.startswith("0x"):
                                pubkey_bytes = "0x" + pubkey_bytes
                            hotkey = subtensor.substrate.ss58_encode(pubkey_bytes, ss58_format=42)
                    except Exception:
                        pass
                
                stake_extrinsic.append({
                    'coldkey': actual_coldkey,
                    'hotkey': hotkey,
                    'type': 'StakeAdded',
                    'netuid': netuid,
                    'amount_tao': amount_staked / 1e9 if amount_staked else 0,
                    'amount_raw': amount_staked,
                    'limit_price': 1e9,
                    'extrinsic_idx': idx,
                })

    return stake_extrinsic

def extract_stake_added_events_from_data(events_data):
    """
    Extract StakeAdded events from the events data.
    
    Args:
        events_data: List of event dictionaries from blockchain
    
    Returns:
        List of dictionaries containing StakeAdded event information
    """
    stake_events = []
    
    for event in events_data:
        event_info = event.get('event', {})
        
        # Check if this is a SubtensorModule StakeAdded event
        if event_info.get('module_id') == 'SubtensorModule' and event_info.get('event_id') == 'StakeAdded':
            attributes = event_info.get('attributes', {})
            
            # Convert coldkey and hotkey to ss58 addresses if possible
            def to_ss58(addr_bytes, ss58_format=42):
                if addr_bytes is None:
                    return None
                pubkey_bytes = bytes(addr_bytes).hex()
                if not pubkey_bytes.startswith("0x"):
                    pubkey_bytes = "0x" + pubkey_bytes
                return subtensor.substrate.ss58_encode(pubkey_bytes, ss58_format=ss58_format)
                
            # The attributes for StakeAdded are a tuple
            # Example: ((coldkey_bytes,), (hotkey_bytes,), amount, stake, netuid, block_number)
            if isinstance(attributes, tuple) and len(attributes) >= 6:
                coldkey_tuple = to_ss58(attributes[0][0]) if isinstance(attributes[0], tuple) and len(attributes[0]) > 0 else attributes[0]
                hotkey_tuple = to_ss58(attributes[1][0]) if isinstance(attributes[1], tuple) and len(attributes[1]) > 0 else attributes[1]
                amount = attributes[2]
                netuid = attributes[4]
                
                stake_events.append({
                    'type': 'StakeAdded',
                    'coldkey': coldkey_tuple,
                    'hotkey': hotkey_tuple,
                    'netuid': netuid,
                    'amount': amount,
                    'amount_tao': amount / 1e9 if amount else 0,
                })
    
    return stake_events

def _create_signature_hash(coldkey, amount, netuid, hotkey):
    """
    Create a hash signature from coldkey, amount, netuid, and hotkey.
    
    Args:
        coldkey: Coldkey address (string)
        amount: Amount in raw units (int)
        netuid: Network UID (int)
        hotkey: Hotkey address (string or None)
    
    Returns:
        Hash string
    """
    # Normalize None values to empty string for hashing
    coldkey = coldkey or ""
    hotkey = hotkey or ""
    amount = amount or 0
    netuid = netuid if netuid is not None else -1
    
    # Create a consistent string representation
    signature_str = f"{coldkey}:{amount}:{netuid}:{hotkey}"
    
    # Create hash
    return hashlib.sha256(signature_str.encode()).hexdigest()

def find_failed_extrinsics(stake_extrinsics, stake_events):
    """
    Find extrinsics that don't have corresponding StakeAdded events.
    These are the failed extrinsics.
    
    Args:
        stake_extrinsics: List of stake extrinsic dictionaries
        stake_events: List of StakeAdded event dictionaries
    
    Returns:
        List of failed extrinsic dictionaries
    """
    failed_extrinsics = []
    coldkeys = []   
    
    # Create a set of hashes from events for quick lookup
    event_hashes = set()
    for event in stake_events:
        coldkey = event.get('coldkey')
        netuid = event.get('netuid')
        amount = event.get('amount')
        hotkey = event.get('hotkey')
        
        if coldkey and netuid is not None and amount is not None:
            event_hash = _create_signature_hash(coldkey, amount, netuid, hotkey)
            event_hashes.add(event_hash)
    
    # Check each extrinsic against events
    for extrinsic in stake_extrinsics:
        coldkey = extrinsic.get('coldkey')
        netuid = extrinsic.get('netuid')
        amount_raw = extrinsic.get('amount_raw')
        hotkey = extrinsic.get('hotkey')
        
        if coldkey and netuid is not None and amount_raw is not None:
            extrinsic_hash = _create_signature_hash(coldkey, amount_raw, netuid, hotkey)
            
            # If no matching event found, this extrinsic failed
            if extrinsic_hash not in event_hashes:
                failed_extrinsics.append(extrinsic)
                if coldkey not in coldkeys:
                    coldkeys.append(coldkey)
    return failed_extrinsics, coldkeys

def print_stake_extrinsic(stake_extrinsic, coldkeys, threshold, netuid, show_balance):
    now_subnet_infos = subtensor.all_subnets()
    prices = [float(subnet_info.price) for subnet_info in now_subnet_infos]
    cash = {}
    if show_balance:
        balances = subtensor.get_balances(*coldkeys)
        stake_infos = subtensor.get_stake_info_for_coldkeys(coldkey_ss58s=coldkeys)
    for extrinsic in stake_extrinsic:
        netuid_val = int(extrinsic['netuid'])
        tao_amount = float(extrinsic['amount_tao'])
        limit_price = float(extrinsic['limit_price']) / 1e9
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
            total_value_str = get_total_value(subtensor, old_coldkey, now_subnet_infos, netuid_val, cash, balances[old_coldkey], stake_infos[old_coldkey])

        # All extrinsics here are failed (no matching event)
        print(f"{color}SN {netuid_val:3d} => {prices[netuid_val]:8.5f} {limit_price:8.5f} {sign}{tao_amount:5.1f}  {coldkey}{reset} {total_value_str}")

      
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

            
        
            # Extract add_stake and add_stake_limit extrinsics
            stake_extrinsics = extract_stake_extrinsic_from_data(extrinsics)
            
            # Extract StakeAdded events
            stake_events = extract_stake_added_events_from_data(events)
            
            # Find failed extrinsics (extrinsics without matching events)
            failed_extrinsics, coldkeys = find_failed_extrinsics(stake_extrinsics, stake_events)
            
            print(f"*{'*'*40}")
            if failed_extrinsics:
                print_stake_extrinsic(failed_extrinsics, coldkeys, threshold, netuid, show_balance)
            subtensor.wait_for_block()
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)