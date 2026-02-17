import requests
import re

from modules.constants import (
    GOOGLE_DOC_ID_BOTS,
    GOOGLE_DOC_ID_OWNER_WALLETS,
    GOOGLE_DOC_ID_OWNER_WALLETS_SS,
    GOOGLE_DOC_ID_OWNER_WALLETS_PS,
)

bots = []
wallet_owners = {}

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
    wallet_owners["5GkZb6S3PSv6stahzWXgMg2PAe8CxEYSp3PXWPJybhLt1xiF"] = "Jeeter"
    wallet_owners["5FLQ2m1ZgVd2qXfE4ZXtxyuqmjjJHycKqFEWvExCiNzUtEEe"] = "Jeeter"
    wallet_owners["5FnWKpesLZj1ZknKJZ6bzF3VucRxgD7VE4MFVDkh3WDbeUbL"] = "Jeeter"
    wallet_owners["5HkGCkce7aKxinYtU588kjt7sy2HKrKgKyhbNoe13kvrPFT2"] = "Jeeter"


def main():
    load_bots_from_gdoc()
    load_wallet_owners_from_gdoc()
    # Dump all wallet_owners (mapping of address->label) into a .txt file as JS "const LABELS = {...};"
    with open('wallet_labels.txt', 'w', encoding='utf-8') as f:
        f.write("const LABELS = {\n")
        for idx, (address, label) in enumerate(wallet_owners.items()):
            # Escape label if needed (not necessary for current use but safe)
            addr_str = address.strip()
            label_str = label.replace('"', '\\"')
            f.write(f'    "{addr_str}": "{label_str}"')
            f.write(",\n")
            
        # Write each bot address as: "address": ""bot
        for bot_address in bots:
            addr_str = bot_address.strip()
            f.write(f'    "{addr_str}": "bot",\n')
        f.write("};\n")

if __name__ == "__main__":
    main()