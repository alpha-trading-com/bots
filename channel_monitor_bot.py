import requests
import time
import json
import re
from datetime import datetime
from typing import List, Dict, Set


from modules.constants import (
    WEBHOOK_URL_AETH_VIP_MESSAGES,
    WEBHOOK_URL_SS_SENSTIVE_MESSAGES,
    WEBHOOK_URL_AETH_NEWS,
    WEBHOOK_URL_AETH_CHAIN_EVENT,
    WEBHOOK_URL_SS_WALLET_TRANSACTIONS,
    WEBHOOK_URL_SS_MINI_WALLET_TRANSACTIONS,
    WEBHOOK_URL_SS_TRANSFER_TRANSACTIONS,
    WEBHOOK_URL_SS_INFOS,
    KEY_WORDS,
    NETWORK,
    BOT_TOKEN,
    GOOGLE_DOC_ID_CHANNELS,
    TARGET_USER_IDS,
)
from modules.discord import send_webhook_message, create_embed



IMPORTANT_CHANNEL_LIST = []

class DiscordCrawler:
    def __init__(self, bot_token: str, target_user_ids: List[str]):
        self.bot_token = bot_token
        self.guild_id = "799672011265015819"
        self.seen_message_ids: List = []
        self.api_urls = []
        self.initial_messages = []
        self.target_user_ids = target_user_ids
        self.channel_list = self.load_channel_list()
        for channel_id in self.channel_list:
            self.api_urls.append(f"https://discord.com/api/v10/channels/{channel_id}/messages")
            empty_set = set()
            self.seen_message_ids.append(empty_set)

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"{self.bot_token}",
            "Content-Type": "application/json"
        }

    def fetch_all_channels(self) -> List[Dict]:
        """Fetch all channels from the Discord guild"""
        
        url = f"https://discord.com/api/v10/guilds/{self.guild_id}/channels"

        retries = 5
        while retries > 0:
            try:
                response = requests.get(url, headers=self.get_headers())

                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error fetching channels: {response.status_code}")
                    print(f"Response: {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Exception while fetching channels: {e}")
                retries -= 1
                time.sleep(2)

        print("Failed to fetch channels after retries")
        return []
    
    def fetch_messages(self, limit: int = 50, api_url: str = "") -> List[Dict]:
        """Fetch recent messages from the channel"""
        headers = self.get_headers()
        params = {"limit": limit}

        retries = 5
        # print(f"api_url: {api_url}")

        while retries > 0:
            # print(f"Retrying {retries} times...")
            try:
                response = requests.get(api_url, headers=headers, params=params)

                print(f"Response: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error response: {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Error fetching messages: {e}")
                retries -= 1
        print("Failed to fetch messages")
        return []
    
    def is_target_user_message(self, message: Dict) -> bool:
        """Check if message is from a target user"""
        author_id = message.get("author", {}).get("id")
        # return True
        return author_id in self.target_user_ids

    def is_twitter_hold(self, message: Dict) -> Dict:
        "Check if message holds twitter url"
        content = message.get("content", "")
        pattern = r'https://x.com/'
        return re.search(pattern, content) is not None

    def is_owner_claimed_message(self, message: Dict) -> bool:
        "Check if message is a owner claimed message"
        content = message.get("content", "")
        pattern = r'claimed ownership of this channel'
        return re.search(pattern, content) is not None

    def is_announcement_message(self, message: Dict) -> bool:
        "Check if message is an announcement message"
        content = message.get("content", "")
        pattern = r'announcement'
        is_announcement = re.search(pattern, content) is not None
        mention_roles = message.get("mention_roles", [])
        if len(mention_roles) > 0:
            is_announcement = True
        return is_announcement

    def is_sensitive_message(self, message: Dict) -> bool:
        "Check if message is a sensitive message"
        global KEY_WORDS
        content = message.get("content", "")
        # Assume KEY_WORDS is a list of sensitive words/phrases defined elsewhere, including phrases like "new team"
        return any(re.search(rf'\b{re.escape(word)}\b', content, re.IGNORECASE) if " " not in word else re.search(rf'(?<!\w){re.escape(word)}(?!\w)', content, re.IGNORECASE) for word in KEY_WORDS)


    def process_new_messages(self, api_url: str, channel_name: int, target_user_ids: List[str]):
        """Process new messages and send to webhook"""
        messages = self.fetch_messages(api_url=api_url)
        if not messages:
            return
        private_track_lists = [
            "1424029936527741043",
            "1316942343466909777",
            "1273724526190006467",
        ]
        new_messages = []
        new_vip_messages = []
        new_message_ids = set()
        new_sensitive_messages = []
        new_infos_messages = []

        for message in messages:
            message_id = message.get("id")
            if not message_id:
                continue

            new_message_ids.add(message_id)

            # Check if this is a new message from a target user
            if (
                message_id not in self.seen_message_ids[channel_name]
                and (self.is_twitter_hold(message) or # twitter hold
                self.is_owner_claimed_message(message) or # owner claimed
                self.is_announcement_message(message)) # announcement
            ):
                new_messages.append(message)
                print(f"Found new message from {message.get('author', {}).get('username', 'Unknown')}: {message.get('content', '')[:50]}...")

            if (
                message_id not in self.seen_message_ids[channel_name]
                and channel_name != 120
                and any(target_user_id == message.get('author', {}).get('id') for target_user_id in target_user_ids)
            ):
                new_vip_messages.append(message)

            if (
                message_id not in self.seen_message_ids[channel_name] and
                any(target_user_id == message.get('author', {}).get('id') for target_user_id in private_track_lists)
            ):
                new_infos_messages.append(message)

            if (
                message_id not in self.seen_message_ids[channel_name] and
                self.is_sensitive_message(message)
            ):
                new_sensitive_messages.append(message)

            if (message_id not in self.seen_message_ids[channel_name] and
                self.channel_list[channel_name] in IMPORTANT_CHANNEL_LIST):
                new_sensitive_messages.append(message)
            


        # Update seen message IDs
        self.seen_message_ids[channel_name].update(new_message_ids)
        
        # Send new messages to webhook
        if new_messages:
            embeds = [
                create_embed(message=msg, channel_id=self.channel_list[channel_name], title="New Message", color=0xffff00) for msg in new_messages]
            send_webhook_message(
                webhook_url=WEBHOOK_URL_AETH_NEWS, 
                content="@everyone New Message",
                embeds=embeds, 
            )
        else:
            print(f"No new messages from {channel_name}")

        if new_vip_messages:
            embeds = [
                create_embed(message=msg, channel_id=self.channel_list[channel_name], title="New VIP Message", color=0xffff00) for msg in new_vip_messages]
            send_webhook_message(
                webhook_url=WEBHOOK_URL_AETH_VIP_MESSAGES, 
                content="@everyone New VIP Message",
                embeds=embeds, 
            )
        else:
            print(f"No new VIP messages from {channel_name}")

        if new_sensitive_messages:
            embeds = [
                create_embed(message=msg, channel_id=self.channel_list[channel_name], title="New Sensitive Message", color=0xffff00) for msg in new_sensitive_messages]
            send_webhook_message(
                webhook_url=WEBHOOK_URL_SS_SENSTIVE_MESSAGES, 
                content="@everyone New Sensitive Message",
                embeds=embeds, 
            )
        else:
            print(f"No new sensitive messages from {channel_name}")

        if new_infos_messages:
            embeds = [
                create_embed(message=msg, channel_id=self.channel_list[channel_name], title="New Infos Message", color=0xffff00) for msg in new_infos_messages]
            send_webhook_message(
                webhook_url=WEBHOOK_URL_SS_INFOS, 
                content="New Infos Message",
                embeds=embeds, 
            )
        else:
            print(f"No new infos messages from {channel_name}")
        return
    
    def run(self, check_interval: int = 60):
        """Run the crawler with specified interval in seconds"""
        print(f"Starting Discord crawler...")
        for i, channel_id in enumerate(self.channel_list):
            if i == 0:
                #continue for the root channel
                continue
            init_messages = self.fetch_messages(api_url=self.api_urls[i])
            self.initial_messages.append(init_messages)

            for message in init_messages:
                message_id = message.get("id")
                if message_id:
                    self.seen_message_ids[i].add(message_id)

        print(f"Initial fetch complete. Found {len(init_messages)} existing messages.")

        # Start monitoring loop
        while True:
            try:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new messages...")
                for i, channel_id in enumerate(self.channel_list):
                    if i == 0:
                        #continue for the root channel
                        continue
                    self.process_new_messages(api_url=self.api_urls[i], channel_name=i, target_user_ids=self.target_user_ids)
                print(f"Waiting {check_interval} seconds until next check...")
            except KeyboardInterrupt:
                print("\nCrawler stopped by user")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                print("Continuing in 60 seconds...")
            time.sleep(check_interval)

    def load_channel_list(self) -> List[str]:    
        """Print all text channels from the guild that are under specific categories"""
        channels = self.fetch_all_channels()
        if not channels:
            print("Warning: Failed to fetch channels")
            return

        allowed_categories = {"1290321693427892358", "1366426072765431808", "1161764488186441768"}
        text_channels = [
            ch for ch in channels
            if ch.get('type') == 0 and str(ch.get('parent_id')) in allowed_categories
        ]

        channel_list = []
        for channel in sorted(text_channels, key=lambda x: x.get('name', '')):
            channel_id = channel.get('id', 'Unknown')
            channel_list.append(channel_id)
        channel_list.remove("1179129432410173541") # subnet role assigne
        channel_list.remove("1161764746819805215") # subnet role assigner
        channel_list.append("1341812134807343114") # price-talk
        return channel_list

def main():
    # Configuration - Replace these with your actual values
    # Load Discord channel list from a Google Doc (expects one channel ID per line)
    import requests

    def load_channel_list_from_gdoc(doc_id: str, api_key: str = None) -> list:
        global IMPORTANT_CHANNEL_LIST
        """
        Fetches the channel list from a public Google Doc.
        The Google Doc should be published to the web as plain text, with each line having:
            channel_id channel_name

        Args:
            doc_id: The Google Doc's ID (from its URL).
            api_key: (Optional) Google API key if you want to use the API, otherwise None for published plain text.
        Returns:
            List of (channel_id, channel_name) tuples.
        """
        if api_key:
            raise NotImplementedError("API key not supported in this loader - use published plain text.")
        else:
            url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
            resp = requests.get(url)
            resp.raise_for_status()
            # Remove UTF-8 BOM if present
            text = resp.text
            if text.startswith('\ufeff'):
                text = text[1:]
            lines = [
                line.strip()
                for line in text.splitlines()
            ]
            output = []
            for line in lines:
                # Expect lines in form: channel_id   #channel_name
                channel_id = line.split(' ', 1)[0]  # split at first '#' character if present
                channel_name = line.split(' ', 1)[1]
                
                # Strip any remaining BOM or whitespace
                channel_id = channel_id.strip('\ufeff').strip()
                output.append(channel_id)
                if channel_name.endswith("important"):
                    IMPORTANT_CHANNEL_LIST.append(channel_id)
            return output

    load_channel_list_from_gdoc(GOOGLE_DOC_ID_CHANNELS)
    # Create and run crawler
    crawler = DiscordCrawler(
        bot_token=BOT_TOKEN,
        target_user_ids=TARGET_USER_IDS
    )
    
    crawler.run(check_interval=10)  # Check every 60 seconds
if __name__ == "__main__":
    main()

