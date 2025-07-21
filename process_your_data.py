import json

# Your JSON data (the data you provided)
block_data = {
  "authorId": None,
  "extrinsicRoot": None,
  "extrinsics": [
    {
      "args": {
        "now": "1752605904000"
      },
      "era": {
        "immortalEra": "0x00"
      },
      "events": [
        {
          "data": [
            {
              "class": "Mandatory",
              "paysFee": "Yes",
              "weight": {
                "proofSize": "1493",
                "refTime": "268717000"
              }
            }
          ],
          "method": {
            "method": "ExtrinsicSuccess",
            "pallet": "system"
          }
        }
      ],
      "hash": "0x74858a8bcfe07280f53dc81f2e7bb2496584efe8d4108c3e8687188ca1be5473",
      "info": {},
      "method": {
        "method": "set",
        "pallet": "timestamp"
      },
      "nonce": None,
      "paysFee": False,
      "signature": None,
      "success": True,
      "tip": None
    },
    {
      "args": {
        "new_coldkey": "5DSayV1RXU3xLasXV95iefTu9j4fhye6YXFstU15zgm92vZS"
      },
      "era": {
        "mortalEra": [
          "32",
          "11"
        ]
      },
      "events": [
        {
          "data": [
            "5HHDxJdhFr7gcAjBu8K7GqrtaBwDPG72voXWpiVcrLN8X7zE",
            "226478"
          ],
          "method": {
            "method": "Withdraw",
            "pallet": "balances"
          }
        },
        {
          "data": [
            "6011247",
            "0"
          ],
          "method": {
            "method": "Scheduled",
            "pallet": "scheduler"
          }
        },
        {
          "data": [
            "5HHDxJdhFr7gcAjBu8K7GqrtaBwDPG72voXWpiVcrLN8X7zE",
            "5DSayV1RXU3xLasXV95iefTu9j4fhye6YXFstU15zgm92vZS",
            "6011247",
            "100000000"
          ],
          "method": {
            "method": "ColdkeySwapScheduled",
            "pallet": "subtensorModule"
          }
        },
        {
          "data": [
            "5HHDxJdhFr7gcAjBu8K7GqrtaBwDPG72voXWpiVcrLN8X7zE",
            "0"
          ],
          "method": {
            "method": "Deposit",
            "pallet": "balances"
          }
        },
        {
          "data": [
            "5HHDxJdhFr7gcAjBu8K7GqrtaBwDPG72voXWpiVcrLN8X7zE",
            "226478",
            "0"
          ],
          "method": {
            "method": "TransactionFeePaid",
            "pallet": "transactionPayment"
          }
        },
        {
          "data": [
            {
              "class": "Operational",
              "paysFee": "Yes",
              "weight": {
                "proofSize": "0",
                "refTime": "452677000"
              }
            }
          ],
          "method": {
            "method": "ExtrinsicSuccess",
            "pallet": "system"
          }
        }
      ],
      "hash": "0x27062643997909c8c2ba64d2932279a414f798193658bff7023e64b05a988f0a",
      "info": {
        "error": "Fee calculation not supported for this network"
      },
      "method": {
        "method": "scheduleSwapColdkey",
        "pallet": "subtensorModule"
      },
      "nonce": "19",
      "paysFee": True,
      "signature": {
        "signature": "0xdac40433620c0c610b1546851ac928ef1a3dca1db02885d501a42011bbccb959c21b480993cc954c28e877952ece659ceba4aebca1ade95b65c5b14951e70c8b",
        "signer": {
          "id": "5HHDxJdhFr7gcAjBu8K7GqrtaBwDPG72voXWpiVcrLN8X7zE"
        }
      },
      "success": True,
      "tip": "0"
    }
  ]
}

def extract_coldkey_swap_scheduled(data):
    """Extract ColdkeySwapScheduled events from the data"""
    coldkey_swaps = []
    
    extrinsics = data.get('extrinsics', [])
    
    for extrinsic in extrinsics:
        events = extrinsic.get('events', [])
        
        for event in events:
            method = event.get('method', {})
            
            # Check if this is a ColdkeySwapScheduled event
            if (method.get('method') == 'ColdkeySwapScheduled' and 
                method.get('pallet') == 'subtensorModule'):
                
                event_data = event.get('data', [])
                
                swap_info = {
                    'extrinsic_hash': extrinsic.get('hash'),
                    'event_data': {
                        'old_coldkey': event_data[0] if len(event_data) > 0 else None,
                        'new_coldkey': event_data[1] if len(event_data) > 1 else None,
                        'amount': event_data[2] if len(event_data) > 2 else None,
                        'delay': event_data[3] if len(event_data) > 3 else None
                    },
                    'extrinsic_info': {
                        'method': extrinsic.get('method', {}).get('method'),
                        'pallet': extrinsic.get('method', {}).get('pallet'),
                        'success': extrinsic.get('success'),
                        'signer': extrinsic.get('signature', {}).get('signer', {}).get('id') if extrinsic.get('signature') else None
                    }
                }
                
                coldkey_swaps.append(swap_info)
    
    return coldkey_swaps

# Extract the coldkey swap data
swaps = extract_coldkey_swap_scheduled(block_data)

# Print the results
print("=== ColdkeySwapScheduled Event Details ===")
for i, swap in enumerate(swaps, 1):
    print(f"\nColdkey Swap #{i}:")
    print(f"Extrinsic Hash: {swap['extrinsic_hash']}")
    print(f"Method: {swap['extrinsic_info']['method']}")
    print(f"Pallet: {swap['extrinsic_info']['pallet']}")
    print(f"Success: {swap['extrinsic_info']['success']}")
    print(f"Signer: {swap['extrinsic_info']['signer']}")
    print(f"Old Coldkey: {swap['event_data']['old_coldkey']}")
    print(f"New Coldkey: {swap['event_data']['new_coldkey']}")
    print(f"Amount: {swap['event_data']['amount']}")
    print(f"Delay: {swap['event_data']['delay']}")

# Save to JSON file
with open('coldkey_swap_result.json', 'w') as f:
    json.dump(swaps, f, indent=2)

print(f"\nExtracted {len(swaps)} ColdkeySwapScheduled event(s) and saved to 'coldkey_swap_result.json'") 