import bittensor as bt

subtensor = bt.subtensor("finney")

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
                    coldkey_tuple = attributes[0][0] if isinstance(attributes[0], tuple) and len(attributes[0]) > 0 else None
                    hotkey_tuple = attributes[1][0] if isinstance(attributes[1], tuple) and len(attributes[1]) > 0 else None
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
                    'coldkey': to_ss58(coldkey_tuple),
                    'hotkey': to_ss58(hotkey_tuple),
                    'netuid': netuid,
                    'amount': amount,
                    'amount_tao': amount / 1e9 if amount else 0,
                })
                
            elif event_id == 'StakeRemoved':
                # Extract unstake information - also a tuple
                if isinstance(attributes, tuple) and len(attributes) >= 6:
                    coldkey_tuple = attributes[0][0] if isinstance(attributes[0], tuple) and len(attributes[0]) > 0 else None
                    hotkey_tuple = attributes[1][0] if isinstance(attributes[1], tuple) and len(attributes[1]) > 0 else None
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
                    'coldkey': to_ss58(coldkey_tuple),
                    'hotkey': to_ss58(hotkey_tuple),
                    'netuid': netuid,
                    'amount': amount,
                    'amount_tao': amount / 1e9 if amount else 0,
                })
                
            elif event_id == 'StakeMoved':
                # Extract stake move information - also a tuple
                if isinstance(attributes, tuple) and len(attributes) >= 6:
                    coldkey_tuple = attributes[0][0] if isinstance(attributes[0], tuple) and len(attributes[0]) > 0 else None
                    from_hotkey_tuple = attributes[1][0] if isinstance(attributes[1], tuple) and len(attributes[1]) > 0 else None
                    to_hotkey_tuple = attributes[3][0] if isinstance(attributes[3], tuple) and len(attributes[3]) > 0 else None
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
                    'coldkey': to_ss58(coldkey_tuple),
                    'from_hotkey': to_ss58(from_hotkey_tuple),
                    'to_hotkey': to_ss58(to_hotkey_tuple),
                    'netuid': netuid,
                    'amount': amount,
                    'amount_tao': amount / 1e9 if amount else 0,
                })
    
    return stake_events

def print_stake_events(stake_events):
    """
    Print stake events in a readable format.
    """
    for event in stake_events:
        if event['type'] == 'StakeAdded':
            print(f"[  ADDED] Coldkey: {event['coldkey']}, "
                  f"Amount: {event['amount_tao']:.2f} TAO, on subnet {event['netuid']}")
                  
        elif event['type'] == 'StakeRemoved':
            print(f"[REMOVED] Coldkey: {event['coldkey']}, "
                  f"Amount: {event['amount_tao']:.2f} TAO from subnet {event['netuid']}")
                  
        # elif event['type'] == 'StakeMoved':
        #     print(f"[  MOVED] Coldkey: {event['coldkey']}, "
        #           f"From: {event['from_hotkey']}, To: {event['to_hotkey']}, "
        #           f"Amount: {event['amount_tao']:.2f} TAO on subnet {event['netuid']}")

if __name__ == "__main__":    
    print("\n=== Live Event Monitoring ===")
    while True:
        block_number = subtensor.get_current_block()
        block_hash = subtensor.substrate.get_block_hash(block_id=block_number)
        events = subtensor.substrate.get_events(block_hash=block_hash)
        
        # Extract stake events from live data
        stake_events = extract_stake_events_from_data(events)
        if stake_events:
            print(f"\n--- Block {block_number} Stake Events ---")
            print_stake_events(stake_events)
        
        subtensor.wait_for_block()