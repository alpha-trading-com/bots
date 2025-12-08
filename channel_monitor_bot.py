import requests
import time
import json
import re
from datetime import datetime
from typing import List, Dict, Set


IMPORTANT_CHANNEL_LIST = []
WEBHOOK_URL_OWN = "https://discord.com/api/webhooks/1444355854387253502/TzAaJT1a-Eya4PC49UamnXybEB6SthXgih8CclHarcXscTqSrI7D6OtTzhAyYf-wchCr"
WEBHOOK_URL_SENSTIVE_MESSAGES = "https://discord.com/api/webhooks/1444902359380656130/nIOCmE9Fn9_j13WXWY_ebm7Ai_YodKQGsSjSgZzCiW953g-uSQXVmlNy7O0aoo8-EBL1"

NETWORK = "finney"
#NETWORK = "ws://34.30.248.57:9944"

KEY_WORDS = ["new team", "ownership", "man in charge", "partner"]
class DiscordCrawler:
    def __init__(self, channel_list: List[str], bot_token: str, webhook_url: str, target_user_ids: List[str]):
        self.channel_list = channel_list
        self.bot_token = bot_token
        self.webhook_url = webhook_url
        self.seen_message_ids: List = []
        self.api_urls = []
        self.initial_messages = []
        self.target_user_ids = target_user_ids
        for channel_id in self.channel_list:
            self.api_urls.append(f"https://discord.com/api/v10/channels/{channel_id}/messages")
            empty_set = set()
            self.seen_message_ids.append(empty_set)

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"{self.bot_token}",
            "Content-Type": "application/json"
        }
    
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

    def create_embed(self, message: Dict, subnet_id: int) -> Dict:
        """Create Discord embed from message data"""
        author = message.get("author", {})
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        message_id = message.get("id", "")
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            formatted_time = timestamp

        color = 0xffff00
        if self.is_twitter_hold(message):
            title = f"New Twitter Posted from **Subnet {subnet_id}**" if subnet_id != 129 else f"New Twitter Posted from **Price-talk**"
            color = 0xffff00
        elif self.is_owner_claimed_message(message):
            title = f"New Owner Claimed Message from **Subnet {subnet_id}**" if subnet_id != 129 else f"New Owner Claimed Message from **Price-talk**"
            color = 0xa832a8
        elif self.is_announcement_message(message):
            title = f"New Announcement Message from **Subnet {subnet_id}**" if subnet_id != 129 else f"New Announcement Message from **Price-talk**"
            color = 0x66aaff
        else:
            title = f"New Unknown Type Message from **Subnet {subnet_id}**" if subnet_id != 129 else f"New Unknown Type Message from **Price-talk**"


        # Create embed
        embed = {
            "title": title,
            "description": content[:4096] if content else "*No text content*",  # Discord embed limit
            "color": color,
            "timestamp": timestamp,
            "author": {
                "name": f"{author.get('global_name', author.get('username', 'Unknown'))}",
                "icon_url": f"https://cdn.discordapp.com/avatars/{author.get('id')}/{author.get('avatar')}.png" if author.get('avatar') else None
            },
            "fields": [
                {
                    "name": "Channel",
                    "value": f"<#{self.channel_list[subnet_id]}>",
                    "inline": True
                }
            ]
        }

        return embed

    def create_embed_private(self, message: Dict, subnet_id: int) -> Dict:
        """Create Discord embed from message data"""
        author = message.get("author", {})
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        message_id = message.get("id", "")
        
        color = 0xffff00
        title = f"New VIP Message from {author.get('global_name', author.get('username', 'Unknown'))}"
        embed = {
            "title": title,
            "description": content[:4096] if content else "*No text content*",  # Discord embed limit
            "color": color,
            "timestamp": timestamp,
            "author": {
                "name": f"{author.get('global_name', author.get('username', 'Unknown'))}",
                "icon_url": f"https://cdn.discordapp.com/avatars/{author.get('id')}/{author.get('avatar')}.png" if author.get('avatar') else None
            },
            "fields": [
                {
                    "name": "Channel",
                    "value": f"<#{self.channel_list[subnet_id]}>",
                    "inline": True
                }
            ]
        }
        return embed

    def create_embed_sensitive(self, message: Dict, subnet_id: int) -> Dict:
        """Create Discord embed from message data"""
        author = message.get("author", {})
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        message_id = message.get("id", "")
        
        color = 0xffff00
        title = f"New Sensitive Message from {author.get('global_name', author.get('username', 'Unknown'))}"
        embed = {
            "title": title,
            "description": content[:4096] if content else "*No text content*",  # Discord embed limit
            "color": color,
            "timestamp": timestamp,
            "author": {
                "name": f"{author.get('global_name', author.get('username', 'Unknown'))}",
                "icon_url": f"https://cdn.discordapp.com/avatars/{author.get('id')}/{author.get('avatar')}.png" if author.get('avatar') else None
            },
            "fields": [
                {
                    "name": "Channel",
                    "value": f"<#{self.channel_list[subnet_id]}>",
                    "inline": True
                }
            ]
        }
        return embed

    def send_webhook_message(self, embeds: List[Dict]):
        """Send message to webhook"""
        if not embeds:
            return
        
        payload = {
            "content": "@everyone ",
            "embeds": embeds,
            "username": "Message Monitor",
            "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png"
        }
        
        retries = 5
        while retries > 0:
            try:
                response = requests.post(self.webhook_url, json=payload)
                if response.status_code in [200, 204]:
                    print(f"Successfully sent {len(embeds)} message(s) to webhook")
                    return
                else:
                    print(f"Failed to send webhook: {response.status_code} {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Error sending webhook: {e}")
                retries -= 1
                time.sleep(2)
        print("Failed to send webhook")

    def send_webhook_message_private(self, embeds: List[Dict]):
        """Send message to webhook"""
        if not embeds:
            return
        payload = {
            "content": "@everyone VIP message",
            "embeds": embeds,
            "username": "Message Monitor",
            "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png"
        }
        retries = 5
        while retries > 0:
            try:
                response = requests.post(WEBHOOK_URL_OWN, json=payload)
                if response.status_code in [200, 204]:
                    print(f"Successfully sent {len(embeds)} message(s) to webhook")
                    return
                else:
                    print(f"Failed to send webhook: {response.status_code} {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Error sending webhook: {e}")
                retries -= 1
                time.sleep(2)
        print("Failed to send webhook")
        return

    def send_webhook_message_sensitive(self, embeds: List[Dict]):
        """Send message to webhook"""
        if not embeds:
            return
        payload = {
            "content": "@everyone Sensitive message",
            "embeds": embeds,
            "username": "Message Monitor",
            "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png"
        }
        retries = 5
        while retries > 0:
            try:
                response = requests.post(WEBHOOK_URL_SENSTIVE_MESSAGES, json=payload)
                if response.status_code in [200, 204]:
                    print(f"Successfully sent {len(embeds)} message(s) to webhook")
                    return
                else:
                    print(f"Failed to send webhook: {response.status_code} {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Error sending webhook: {e}")
                retries -= 1
                time.sleep(2)
        print("Failed to send webhook")
        return

    def process_new_messages(self, api_url: str, channel_name: int, target_user_ids: List[str]):
        """Process new messages and send to webhook"""
        messages = self.fetch_messages(api_url=api_url)
        if not messages:
            return
        global IMPORTANT_CHANNEL_LIST

        new_messages = []
        new_vip_messages = []
        new_message_ids = set()
        new_sensitive_messages = []

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
        # for messages in new_message_ids:
        #     print(f"message = {messages}")

            if (
                message_id not in self.seen_message_ids[channel_name] and
                any(target_user_id == message.get('author', {}).get('id') for target_user_id in target_user_ids)
            ):
                new_vip_messages.append(message)

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
            embeds = [self.create_embed(message=msg, subnet_id=channel_name) for msg in new_messages]
            self.send_webhook_message(embeds)
        else:
            print(f"No new messages from {channel_name}")

        if new_vip_messages:
            embeds = [self.create_embed_private(message=msg, subnet_id=channel_name) for msg in new_vip_messages]
            self.send_webhook_message_private(embeds)
        else:
            print(f"No new VIP messages from {channel_name}")

        if new_sensitive_messages:
            embeds = [self.create_embed_sensitive(message=msg, subnet_id=channel_name) for msg in new_sensitive_messages]
            self.send_webhook_message_sensitive(embeds)
        else:
            print(f"No new sensitive messages from {channel_name}")
        return
    
    def run(self, check_interval: int = 60):
        """Run the crawler with specified interval in seconds"""
        print(f"Starting Discord crawler...")
        for i, channel_id in enumerate(self.channel_list):
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
                    self.process_new_messages(api_url=self.api_urls[i], channel_name=i, target_user_ids=self.target_user_ids)
                print(f"Waiting {check_interval} seconds until next check...")
            except KeyboardInterrupt:
                print("\nCrawler stopped by user")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                print("Continuing in 60 seconds...")
            time.sleep(check_interval)


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

    # Replace this with your Doc ID (publish it as plain text!)
    GOOGLE_DOC_ID = "1c-KDhGKINbJRKlXBtsLahyuNIZg3ptRic1ZwM1PpWo4"

    # Loads the channel list from the Google Doc
    CHANNEL_LIST = load_channel_list_from_gdoc(GOOGLE_DOC_ID)
    BOT_TOKEN = "MTIwNjY0MzY5NDEyODg1NzEwMw.GkBLIU.9yxK6xuxJbqYOJ7IcBFekUufJqNRCu-YqNE_I8"  # Your bot token
    WEBHOOK_URL = "https://discord.com/api/webhooks/1440684964784902299/oqS9xREAL46lsroqnsKfjuJ35xFSmXGj135qKqHk_UKwQ0oB--GY20n9m38pjqBRx-Ip"  # Replace with your webhook URL
    
    # List of user IDs to monitor (from your output example)
    TARGET_USER_IDS = [
        "389189199514959893",  # const
        "1020187154502144072", # Tegridy
        #"1438183192610734211",  # soon
    ]
    
    # Create and run crawler
    crawler = DiscordCrawler(
        channel_list=CHANNEL_LIST,
        bot_token=BOT_TOKEN,
        webhook_url=WEBHOOK_URL,
        target_user_ids=TARGET_USER_IDS
    )
    
    crawler.run(check_interval=10)  # Check every 60 seconds
if __name__ == "__main__":
    main()

