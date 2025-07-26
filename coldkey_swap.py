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
        self.subtensor = bt.subtensor("archive")
        self.subtensor_finney = bt.subtensor("finney")

        self.last_checked_block = self.subtensor.get_current_block() - 1
        self.discord_bot = DiscordBot()
        self.owner_coldkeys = self.get_owner_coldkeys()       
        self.thread = threading.Thread(target=self.fetch_owner_coldkeys, daemon=True)

    def fetch_owner_coldkeys(self):
        print("Running fetch_owner_coldkeys thread")
        while True:
            self.owner_coldkeys = self.get_owner_coldkeys()
            time.sleep(300)

    def get_owner_coldkeys(self):
        print("Getting owner coldkeys")
        owner_coldkeys = []
        subnet_infos = self.subtensor_finney.get_all_subnets_info()
        for subnet_info in subnet_infos:
            owner_coldkeys.append(subnet_info.owner_ss58)
        print("Fetched owner coldkeys")
        return owner_coldkeys
    

    def fetch_extrinsic_data(self, block_number):
        """Extract ColdkeySwapScheduled events from the data"""
        coldkey_swaps = []
        block_hash = self.subtensor.substrate.get_block_hash(block_id=block_number)
        extrinsics = self.subtensor.substrate.get_extrinsics(block_hash=block_hash)
       
        for ex in extrinsics:
            call = ex.value.get('call', {})
            if (
                call.get('call_module') == 'SubtensorModule' and
                call.get('call_function') == 'schedule_swap_coldkey'
            ):
                # Get the new coldkey from call_args
                args = call.get('call_args', [])
                new_coldkey = next((a['value'] for a in args if a['name'] == 'new_coldkey'), None)
                from_coldkey = ex.value.get('address', None)
                print(f"Swap scheduled: from {from_coldkey} to {new_coldkey}")
                swap_info = {
                    'old_coldkey': from_coldkey,
                    'new_coldkey': new_coldkey,
                    'subnet': self.owner_coldkeys.index(from_coldkey),
                }
                
                coldkey_swaps.append(swap_info)
        
        return coldkey_swaps
 
    def run(self):
        self.thread.start()
        print("Thread started")

        while True:
                current_block = self.subtensor.get_current_block()
                if current_block < self.last_checked_block:
                    time.sleep(1)
                    continue

                print(f"Fetching coldkey swaps for block {self.last_checked_block}")
                while True:
                    try:
                        coldkey_swaps = self.fetch_extrinsic_data(self.last_checked_block)
                        if len(coldkey_swaps) > 0:
                            try:
                                with open("coldkey_swaps.log", "a") as f:
                                    for swap in coldkey_swaps:
                                        f.write(f"{swap}\n")
                            except Exception as e:
                                print(f"Error writing to file: {e}")

                            try:
                                message = self.format_message(coldkey_swaps)
                                self.discord_bot.send_message(message)
                            except Exception as e:
                                print(f"Error sending message: {e}")
                        else:
                            print("No coldkey swaps found")
                        
                        self.last_checked_block += 1
                        break
                    except Exception as e:
                        print(f"Error fetching coldkey swaps: {e}")
                        time.sleep(1)
        time.sleep(1)

    def format_message(self, coldkey_swaps):
        message = "Hey @everyone! \n"
        for swap in coldkey_swaps:
            message += f"Subnet {swap['subnet']} is swapping coldkey from {swap['old_coldkey']} to {swap['new_coldkey']}\n"
        return message


if __name__ == "__main__":
    fetcher = ColdkeySwapFetcher()
    fetcher.run()