import bittensor as bt

subtensor = bt.subtensor("finney")

bots = [
    "5FjxQ1fPgbttCsA5CsB2roGGmaZei5cxV3TDNUPQ7mmhux4L", #Bots
    "5GuLYhyfPPMRqu9j57FUBLvQgx3wDjgL3WvqoyKnLjpuYeET",
    "5C9xYZAkGGG3dpnkpLDCHqZjD1FvsX8oe9HnHXXr7jaCCvym",
    "5DkaS1EP5p7ehaYQVuhJGh2Dbsq7qZtyvRHpsnRw8idM2AAx",
    "5DDDpkANMCJZjK4dAcHGMJNahD4ATWQyksAyiaDh9iMNRMzK",
]

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
                pubkey_bytes = bytes(addr_bytes).hex()
                if not pubkey_bytes.startswith("0x"):
                    pubkey_bytes = "0x" + pubkey_bytes
                return subtensor.substrate.ss58_encode(pubkey_bytes, ss58_format=ss58_format)
                
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

def print_stake_events(stake_events, netuid):
    """
    Print stake events in a readable format.
    """
    for event in stake_events:
        netuid = int(event['netuid'])

        tao_amount = float(event['amount_tao'])
        coldkey = event['coldkey']
        
        if coldkey in bots:
            coldkey = coldkey + "(bot)"

        if event['type'] == 'StakeAdded':
            tao_amount = tao_amount
        elif event['type'] == 'StakeRemoved':
            tao_amount = -tao_amount
        else:
            continue
        
        if (netuid == netuid or netuid == -1) and (abs(tao_amount) > threshold or threshold == -1):
            print(f"SN {netuid:3d} => {tao_amount:+8.5f}  {coldkey}")
                  
if __name__ == "__main__":    
    netuid = int(input("Enter the netuid: "))
    threshold = float(input("Enter the threshold: "))
    
    while True:
        block_number = subtensor.get_current_block()
        block_hash = subtensor.substrate.get_block_hash(block_id=block_number)
        events = subtensor.substrate.get_events(block_hash=block_hash)
        
        # Extract stake events from live data
        stake_events = extract_stake_events_from_data(events)
        if stake_events:
            print(f"***")
            print_stake_events(stake_events, netuid)
        
        subtensor.wait_for_block()