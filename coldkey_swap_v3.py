import bittensor as bt
import os
import requests
import json
from constants import USERS, WEBHOOK_URL
from twitter_bot.twitter_bot_x import TwitterBotX
import time
import threading
import requests


TAOSTAS_API = "tao-20304005-d9a1-4629-b08d-4a828a9b628e:d201be87"
WEBHOOK_URL = "https://discord.com/api/webhooks/1396875737952292936/Bggfi9QEHVljmOxaqzJniLwQ70oCjnlj0lb7nIBq4avsVya_dkGNfjOKaGlOt_urwdul"
NETWORK = "ws://34.30.248.57:9944"
SLEEP_TIME = 48


TAOSTATS_APIS = [
    "tao-b9e1c93a-8542-424f-9cbf-04c52c0b0eff:70c737dd",
    "tao-8a34e4f6-41bd-49c6-bbd7-625c07c198b6:23cb8cfc",
    "tao-08e84b70-1818-44e8-8d77-592a7226de79:01bdc313",
    "tao-3c59299a-3580-434f-8d73-91c168f4ac95:772bf163",
    "tao-ca48e2a2-fe87-41a4-8799-db25c086cfe1:850b76fd",
    "tao-8da14397-fd00-4063-8409-5d10c7ff5161:6fb31bc1",
    "tao-82be3dfa-4ac1-4acd-902e-193349420ee6:04e1585b",
    "tao-0ff0e3c6-b46b-494c-b209-8917d29b69e4:d8dd4aca",
    "tao-0f28da94-48bd-407a-99b5-2e9f46dfc60c:c5cb3314",
    "tao-6cd08888-1304-4d21-93c2-8732ddf48fd6:1a93ee64",
    "tao-848794ea-6267-493e-a4fe-2c4d91e91bfa:cc80ff4f",
    "tao-cf44a08e-901e-433b-9cde-4ea75b85ff98:e18f49b9"
]


class DiscordBot:
    def __init__(self):
        self.webhook_url = WEBHOOK_URL

    def send_message(self, content):
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



class ColdkeySwapFetcher:
    def __init__(self):
        self.subtensor = bt.subtensor("finney")

        self.last_checked_block = self.subtensor.get_current_block() - 1
        self.discord_bot = DiscordBot()
        self.subnet_names = []
        self.taostats_api_req_count = 0

        
    def get_taostats_api_key(self):
        self.taostats_api_req_count += 1
        return TAOSTATS_APIS[self.taostats_api_req_count % len(TAOSTATS_APIS)]

    def get_subnet_id(self, coldkey):
        try:
            subnet_infos = self.subtensor.all_subnets()
            owner_coldkeys = [subnet_info.owner_coldkey for subnet_info in subnet_infos]
            return owner_coldkeys.index(coldkey)
        except:
            return -1


    def get_coldkey_swaps(self):
        start_block = self.last_checked_block
        end_block = self.subtensor.get_current_block()
        if end_block <=  start_block:
            return []

        print(f"Fetching coldkey swaps for block {start_block} to {end_block}")

        # [start_block, end_block)
        url = f"https://api.taostats.io/api/v1/live/blocks?block_start={start_block}&block_end={end_block}"

        headers = {
            "accept": "application/json",
            "Authorization": self.get_taostats_api_key()
        }

        response = requests.get(url, headers=headers)

        response.raise_for_status()

        """Extract all ColdkeySwapScheduled events from blockchain data"""
        coldkey_swaps = []
        
        data = json.loads(response.text)
        
        # Iterate through all blocks
        for block in data:
            # Check if block has extrinsics
            if 'extrinsics' in block:
                for extrinsic in block['extrinsics']:
                    # Check if extrinsic has events
                    if 'events' in extrinsic:
                        for event in extrinsic['events']:
                            # Look for ColdkeySwapScheduled events
                            if (event.get('method', {}).get('method') == 'ColdkeySwapScheduled'):
                                # Extract the event data
                                event_data = event.get('data', [])
                                if len(event_data) >= 4:
                                    swap_info = {
                                        'old_coldkey': event_data[0],
                                        'new_coldkey': event_data[1], 
                                        'subnet': self.get_subnet_id(event_data[0])
                                    }
                                    coldkey_swaps.append(swap_info)
        self.last_checked_block = end_block
        return coldkey_swaps

    def get_subnet_identities(self):
        print("Getting subnet identities")
        url = "https://api.taostats.io/api/subnet/identity/v1"

        headers = {
            "accept": "application/json",
            "Authorization": self.get_taostats_api_key()
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        payload = json.loads(response.text)
        current_subnet_names = []
        for info in payload.get('data', []):
            current_subnet_names.append(info.get('subnet_name'))

        subnet_count = len(self.subnet_names)
        identity_changes = []
        for i in range(subnet_count):
            if current_subnet_names[i] != self.subnet_names[i]:
                identity_change_info = {
                    'subnet': i,
                    'old_identity': self.subnet_names[i],
                    'new_identity': current_subnet_names[i],
                }
                identity_changes.append(identity_change_info)

        self.subnet_names = current_subnet_names

        return identity_changes


    def run(self):
        while True:
            print("\n\n===============================")
            coldkey_swaps = []
            identity_changes = []   
            try:
                coldkey_swaps = self.get_coldkey_swaps()
            except Exception as e:
                print(f"Error fetching coldkey swaps: {e}")

            try:
                identity_changes = self.get_subnet_identities()
            except Exception as e:
                print(f"Error fetching identity changes: {e}")

            if len(coldkey_swaps) > 0 or len(identity_changes) > 0:
                try:
                    with open("coldkey_swaps.log", "a") as f:
                        for swap in coldkey_swaps:
                            f.write(f"{swap}\n")
                except Exception as e:
                    print(f"Error writing to file: {e}")

                try:
                    with open("identity_changes.log", "a") as f:
                        for change in identity_changes:
                            f.write(f"{change}\n")
                except Exception as e:
                    print(f"Error writing to file: {e}")

                try:
                    message = self.format_message(coldkey_swaps, identity_changes)
                    self.discord_bot.send_message(message)
                except Exception as e:
                    print(f"Error sending message: {e}")
            else:
                print("No coldkey swaps or identity changes found")
            
            time.sleep(SLEEP_TIME)



    def format_message(self, coldkey_swaps, identity_changes):
        message = "Hey @everyone! \n"
        for swap in coldkey_swaps:
            message += f"Subnet {swap['subnet']} is swapping coldkey from {swap['old_coldkey']} to {swap['new_coldkey']}\n"

        for change in identity_changes:
            message += f"Subnet {change['subnet']} has changed identity from {change['old_identity']} to {change['new_identity']}\n"
        return message


if __name__ == "__main__":
    fetcher = ColdkeySwapFetcher()
    #print(fetcher.get_subnet_id("5FYzKTYgH1UCMcJyqJW4v43o4cvjXgEwngM8XBh1cx6pmJpF"))
    fetcher.run()