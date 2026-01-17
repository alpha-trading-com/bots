import sys
import os

# Add parent directory to path to import constants
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import time
from typing import List, Dict, Optional

from dotenv import load_dotenv

load_dotenv(f"{os.path.dirname(os.path.abspath(__file__))}/bot.env")

class DiscordBot:
    def __init__(self):
        self.bot_token = "Bot " + os.getenv("BOT_TOKEN")
        print(self.bot_token)
        self.api_base = f"https://discord.com/api/v10"
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Discord API requests"""
        return {
            "Authorization": self.bot_token,
            "Content-Type": "application/json"
        }
    
    def _get_bot_user_id(self) -> Optional[str]:
        """Get the bot's own user ID"""
        headers = self.get_headers()
        url = f"{self.api_base}/users/@me"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get("id")
        except Exception as e:
            print(f"Error getting bot user ID: {e}")
        
        return None
    
    def get_all_guild_members(self, guild_id: str) -> List[Dict[str, str]]:
        """
        Get all members in a Discord server (guild)
        
        REQUIRED PERMISSIONS:
        - Server Members Intent (Privileged Intent) must be enabled in Discord Developer Portal:
          https://discord.com/developers/applications -> Your Bot -> Bot -> Privileged Gateway Intents
          -> Enable "Server Members Intent"
        - Bot role in the server needs basic access (View Channels permission)
        
        Note: Discord REST API limits this to 1000 members. For larger servers,
        you may need to use the Gateway API or search members.
        
        Args:
            guild_id: The Discord server (guild) ID
        
        Returns:
            List of dictionaries with 'user_id' and 'username' keys
            Example: [{'user_id': '123456789', 'username': 'user#1234', 'display_name': 'Display Name'}, ...]
        """
        headers = self.get_headers()
        all_members = []
        after = None  # For pagination
        
        print(f"Fetching all members from guild {guild_id}...")
        
        while True:
            params = {"limit": 1000}  # Max limit per request
            if after:
                params["after"] = after
            
            retries = 5
            members_batch = []
            
            while retries > 0:
                try:
                    url = f"{self.api_base}/guilds/{guild_id}/members"
                    response = requests.get(url, headers=headers, params=params)
                    
                    if response.status_code == 200:
                        members_batch = response.json()
                        break
                    elif response.status_code == 429:  # Rate limited
                        retry_after = float(response.headers.get("Retry-After", 1))
                        print(f"Rate limited. Waiting {retry_after} seconds...")
                        time.sleep(retry_after)
                        continue
                    elif response.status_code == 403:
                        print(f"✗ Permission denied: Cannot fetch members from guild {guild_id} (403 Forbidden). Bot lacks required permissions.")
                        return []
                    elif response.status_code == 404:
                        print(f"✗ Guild {guild_id} not found (404 Not Found)")
                        return []
                    else:
                        print(f"Error fetching members: {response.status_code} - {response.text}")
                        retries -= 1
                        time.sleep(2)
                except Exception as e:
                    print(f"Exception fetching members: {e}")
                    retries -= 1
                    time.sleep(2)
            
            if not members_batch:
                break
            
            # Process members and extract user info
            for member in members_batch:
                user = member.get("user", {})
                if user:  # Some members might not have user data
                    user_id = user.get("id")
                    username = user.get("username", "Unknown")
                    discriminator = user.get("discriminator", "0")
                    # Format: username#discriminator (or just username if discriminator is 0)
                    if discriminator and discriminator != "0":
                        full_username = f"{username}#{discriminator}"
                    else:
                        full_username = username
                    
                    # Get display name (nickname) if available, otherwise use username
                    display_name = member.get("nick") or username
                    
                    all_members.append({
                        "user_id": user_id,
                        "username": full_username,
                        "display_name": display_name,
                        "global_name": user.get("global_name"),  # Discord's global display name
                    })
            
            print(f"Fetched {len(members_batch)} members (total so far: {len(all_members)})...")
            
            # If we got fewer than 1000 members, we've reached the end
            if len(members_batch) < 1000:
                break
            
            # Set after to the last member's user ID for next pagination
            if members_batch:
                last_member = members_batch[-1]
                last_user = last_member.get("user", {})
                if last_user:
                    after = last_user.get("id")
                else:
                    break
            else:
                break
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
        
        print(f"✓ Total members fetched: {len(all_members)}")
        return all_members
    
    def fetch_messages(self, limit: int = 100, before: str = None, channel_id: str = None) -> List[Dict]:
        """
        Fetch messages from the channel
        
        Args:
            limit: Number of messages to fetch (max 100)
            before: Message ID to fetch messages before (for pagination)
        
        Returns:
            List of message dictionaries
        """
        headers = self.get_headers()
        params = {"limit": limit}
        if before:
            params["before"] = before
        
        retries = 5
        while retries > 0:
            try:
                response = requests.get(f"{self.api_base}/channels/{channel_id}/messages", headers=headers, params=params)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    retry_after = float(response.headers.get("Retry-After", 1))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"Error fetching messages: {response.status_code} - {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Error fetching messages: {e}")
                retries -= 1
                time.sleep(2)
        
        print("Failed to fetch messages")
        return []

    def send_message(self, content: str, channel_id: str = None, embeds: List[Dict] = None) -> Optional[str]:
        """
        Send a message to a Discord channel
        
        Args:
            content: Message content/text
            channel_id: Channel ID to send to (uses self.channel_id if not provided)
            embeds: Optional list of embed dictionaries
        
        Returns:
            Message ID if successful, None otherwise
        """
        headers = self.get_headers()
        url = f"{self.api_base}/channels/{channel_id}/messages"
        
        payload = {"content": content}
        if embeds:
            payload["embeds"] = embeds
        
        retries = 5
        while retries > 0:
            try:
                response = requests.post(url, headers=headers, json=payload)
                
                if response.status_code in [200, 201]:
                    message_data = response.json()
                    message_id = message_data.get("id")
                    print(f"✓ Message sent to channel {channel_id}")
                    return message_id
                elif response.status_code == 429:  # Rate limited
                    retry_after = float(response.headers.get("Retry-After", 1))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"Error sending message: {response.status_code} - {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Exception sending message: {e}")
                retries -= 1
                time.sleep(2)
        
        print("Failed to send message")
        return None
    
    def send_dm(self, user_id: str, content: str, embeds: List[Dict] = None) -> Optional[str]:
        """
        Send a direct message (DM) to a user
        
        Args:
            user_id: Discord user ID to send DM to
            content: Message content/text
            embeds: Optional list of embed dictionaries
        
        Returns:
            Message ID if successful, None otherwise
        """
        headers = self.get_headers()
        
        # Step 1: Create DM channel with the user
        dm_channel_url = f"{self.api_base}/users/@me/channels"
        dm_payload = {"recipient_id": user_id}
        
        retries = 5
        dm_channel_id = None
        
        while retries > 0:
            try:
                response = requests.post(dm_channel_url, headers=headers, json=dm_payload)
                
                if response.status_code in [200, 201]:
                    dm_data = response.json()
                    dm_channel_id = dm_data.get("id")
                    break
                elif response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 1))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"Error creating DM channel: {response.status_code} - {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Exception creating DM channel: {e}")
                retries -= 1
                time.sleep(2)
        
        if not dm_channel_id:
            print("Failed to create DM channel")
            return None
        
        # Step 2: Send message to the DM channel
        message_url = f"{self.api_base}/channels/{dm_channel_id}/messages"
        payload = {"content": content}
        if embeds:
            payload["embeds"] = embeds
        
        retries = 5
        while retries > 0:
            try:
                response = requests.post(message_url, headers=headers, json=payload)
                
                if response.status_code in [200, 201]:
                    message_data = response.json()
                    message_id = message_data.get("id")
                    print(f"✓ DM sent to user {user_id}")
                    return message_id
                elif response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 1))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"Error sending DM: {response.status_code} - {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Exception sending DM: {e}")
                retries -= 1
                time.sleep(2)
        
        print("Failed to send DM")
        return None
    
    def _get_dm_channel_id(self, user_id: str) -> Optional[str]:
        """
        Get or create DM channel with a user
        
        Args:
            user_id: Discord user ID
        
        Returns:
            DM channel ID or None if failed
        """
        headers = self.get_headers()
        dm_channel_url = f"{self.api_base}/users/@me/channels"
        dm_payload = {"recipient_id": user_id}
        
        retries = 5
        while retries > 0:
            try:
                response = requests.post(dm_channel_url, headers=headers, json=dm_payload)
                
                if response.status_code in [200, 201]:
                    dm_data = response.json()
                    return dm_data.get("id")
                elif response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 1))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"Error getting DM channel: {response.status_code} - {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Exception getting DM channel: {e}")
                retries -= 1
                time.sleep(2)
        
        return None
    
    def get_messages_sent_to_user(self, user_id: str, limit: int = 100) -> List[Dict]:
        """
        Get messages that the bot sent to a specific user (in DMs)
        
        Args:
            user_id: Discord user ID to get messages for
            limit: Maximum number of messages to fetch (max 100 per request)
        
        Returns:
            List of message dictionaries that the bot sent to this user
        """
        # Get DM channel ID
        dm_channel_id = self._get_dm_channel_id(user_id)
        if not dm_channel_id:
            print(f"Failed to get DM channel with user {user_id}")
            return []
        
        # Get bot's user ID to filter messages
        bot_user_id = self._get_bot_user_id()
        if not bot_user_id:
            print("Warning: Could not get bot user ID. Cannot filter bot messages.")
            return []
        
        # Fetch messages from DM channel
        all_messages = []
        before = None
        
        while len(all_messages) < limit:
            batch_limit = min(100, limit - len(all_messages))
            messages = self.fetch_messages(limit=batch_limit, before=before, channel_id=dm_channel_id)
            
            if not messages:
                break
            
            # Filter to only messages sent by the bot
            bot_messages = [
                msg for msg in messages 
                if msg.get("author", {}).get("id") == bot_user_id
            ]
            all_messages.extend(bot_messages)
            
            # If we got fewer messages than requested, we've reached the end
            if len(messages) < batch_limit:
                break
            
            # Set before to the oldest message ID for next pagination
            before = messages[-1].get("id")
        
        print(f"Found {len(all_messages)} messages sent to user {user_id}")
        return all_messages[:limit]
    
    def delete_message(self, message_id: str, channel_id: str = None) -> bool:
        """
        Delete a single message
        
        Args:
            message_id: ID of the message to delete
            channel_id: Channel ID where the message is (required)
        
        Returns:
            True if successful, False otherwise
        """
        if not channel_id:
            print("Error: channel_id is required for message deletion")
            return False
        
        headers = self.get_headers()
        url = f"{self.api_base}/channels/{channel_id}/messages/{message_id}"
        
        retries = 5
        while retries > 0:
            try:
                response = requests.delete(url, headers=headers)
                
                if response.status_code in [200, 204]:
                    return True
                elif response.status_code == 429:  # Rate limited
                    retry_after = float(response.headers.get("Retry-After", 1))
                    print(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                elif response.status_code == 403:  # Permission denied
                    print(f"✗ Permission denied: Cannot delete message {message_id} (403 Forbidden). Bot lacks required permissions.")
                    return False  # Break immediately without retrying
                elif response.status_code == 404:
                    print(f"Message {message_id} not found (may already be deleted)")
                    return True  # Consider it successful if already deleted
                else:
                    print(f"Error deleting message {message_id}: {response.status_code} - {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Exception deleting message {message_id}: {e}")
                retries -= 1
                time.sleep(2)
        
        return False
    
    def delete_all_messages(self, batch_delay: float = 0.5, channel_id: str = None, bot_only: bool = False):
        """
        Delete all messages in the channel
        
        Args:
            batch_delay: Delay between batches of deletions (in seconds)
            channel_id: Channel ID to delete from (uses self.channel_id if not provided)
            bot_only: If True, only delete messages sent by the bot
        """

        
        print(f"Starting to delete messages from channel {channel_id}...")
        if bot_only:
            print("Mode: Bot messages only")
        
        # Get bot's own user ID for bot_only mode
        bot_user_id = None
        if bot_only:
            bot_user_id = self._get_bot_user_id()
            if not bot_user_id:
                print("Warning: Could not get bot user ID. bot_only mode may not work correctly.")

        
        total_deleted = 0
        total_failed = 0
        before = None
        
        while True:
            # Fetch a batch of messages
            messages = self.fetch_messages(limit=100, before=before, channel_id=channel_id)
            
            if not messages:
                print("No more messages to fetch.")
                break
            
            print(f"Fetched {len(messages)} messages. Starting deletion...")
            
            # Delete each message in the batch
            for message in messages:
                message_id = message.get("id")
                if not message_id:
                    continue
                
                # Get message info for logging
                author = message.get("author", {})
                author_id = author.get("id")
                author_name = author.get("username", "Unknown")
                content_preview = message.get("content", "")[:50]
                
                # Skip if bot_only mode and message is not from bot
                if bot_only and bot_user_id and author_id != bot_user_id:
                    continue
                
                if self.delete_message(message_id, channel_id=channel_id):
                    total_deleted += 1
                    print(f"✓ Deleted message from {author_name}: {content_preview}... ({total_deleted} total)")
                else:
                    total_failed += 1
                    print(f"✗ Failed to delete message {message_id} ({total_failed} failed)")
                
                # Small delay to avoid hitting rate limits
                time.sleep(0.1)
            
            # Set before to the oldest message ID for next pagination
            if messages:
                before = messages[-1].get("id")
            
            # Delay between batches
            if len(messages) == 100:  # If we got a full batch, there might be more
                print(f"Waiting {batch_delay} seconds before fetching next batch...")
                time.sleep(batch_delay)
            else:
                # Last batch
                break
        
        print(f"\n=== Deletion Complete ===")
        print(f"Total deleted: {total_deleted}")
        print(f"Total failed: {total_failed}")
    
    def _contains_banned_keywords(self, message_content: str) -> bool:
        """
        Check if a message contains any banned keywords (case-insensitive)
        
        Args:
            message_content: The content of the message to check
        
        Returns:
            True if message contains banned keywords, False otherwise
        """
        if not message_content:
            return False
        
        message_lower = message_content.lower()
        for keyword in BANNED_KEYWORDS:
            if keyword.lower() in message_lower:
                return True
        
        return False

    def _contains_github_url(self, message_content: str) -> bool:
        """
        Check if a message contains a GitHub URL.

        Args:
            message_content: The content of the message to check

        Returns:
            True if message contains a GitHub URL, False otherwise
        """
        if not message_content:
            return False

        github_url_indicators = [
            "https://github.com/",
            "http://github.com/",
            "github.com/"
        ]
        message_lower = message_content.lower()
        for indicator in github_url_indicators:
            if indicator in message_lower:
                return True
        return False
    
    def delete_messages_with_keywords_in_channel(self, channel_id: str, batch_delay: float = 0.5, limit: Optional[int] = None):
        """
        Delete messages containing banned keywords from a channel
        
        Args:
            channel_id: Channel ID to scan and delete from
            batch_delay: Delay between batches of deletions (in seconds)
            limit: Maximum number of messages to scan (None for unlimited)
        """
        print(f"Starting to scan and delete messages with banned keywords from channel {channel_id}...")
        print(f"Banned keywords: {', '.join(BANNED_KEYWORDS)}")
        
        total_scanned = 0
        total_deleted = 0
        total_failed = 0
        before = None
        
        while True:
            # Check if we've reached the limit
            if limit and total_scanned >= limit:
                print(f"Reached scan limit of {limit} messages")
                break
            
            # Fetch a batch of messages
            batch_limit = min(100, limit - total_scanned if limit else 100)
            messages = self.fetch_messages(limit=batch_limit, before=before, channel_id=channel_id)
            
            if not messages:
                print("No more messages to fetch.")
                break
            
            print(f"Fetched {len(messages)} messages. Scanning for banned keywords...")
            
            # Check and delete messages containing banned keywords
            for message in messages:
                total_scanned += 1
                message_id = message.get("id")
                if not message_id:
                    continue
                
                # Get message content
                content = message.get("content", "")
                
                # Check if message contains banned keywords
                if self._contains_banned_keywords(content) or self._contains_github_url(content):
                    # Get message info for logging
                    author = message.get("author", {})
                    author_name = author.get("username", "Unknown")
                    content_preview = content[:50]
                    
                    if self.delete_message(message_id, channel_id=channel_id):
                        total_deleted += 1
                        print(f"✓ Deleted message from {author_name} (contains banned keyword): {content_preview}... ({total_deleted} total)")
                    else:
                        total_failed += 1
                        print(f"✗ Failed to delete message {message_id} ({total_failed} failed)")
                    
                    # Small delay to avoid hitting rate limits
                    time.sleep(0.1)
            
            # Set before to the oldest message ID for next pagination
            if messages:
                before = messages[-1].get("id")
            
            # Delay between batches
            if len(messages) == 100:  # If we got a full batch, there might be more
                print(f"Scanned {total_scanned} messages. Waiting {batch_delay} seconds before fetching next batch...")
                time.sleep(batch_delay)
            else:
                # Last batch
                break
        
        print(f"\n=== Keyword Filtering Complete ===")
        print(f"Total scanned: {total_scanned}")
        print(f"Total deleted: {total_deleted}")
        print(f"Total failed: {total_failed}")

    def clears(self, user_id: str):
        """
        Clear all messages in a DM
        
        Args:
            user_id: Discord user ID
        """
        dm_channel_id = self._get_dm_channel_id(user_id)
        if not dm_channel_id:
            print(f"Failed to get DM channel with user {user_id}")
            return
        self.delete_all_messages(channel_id=dm_channel_id)
        print(f"Cleared all messages in DM with user {user_id}")
        return True


def main():
    """
    Main function to run the message deleter
    Configure your bot token and channel ID here
        """    
    # Create deleter instance
    discord_bot = DiscordBot()
    
    print(discord_bot.get_all_guild_members(guild_id="1420796398307377284"))
    # # discord_bot.send_message(content="Hello, I am here to let you know the important news and events. :heart:", channel_id="1447606805248086218")
    # discord_bot.send_dm(user_id=user_id, content=message)
    # channel_id = discord_bot._get_dm_channel_id(user_id=user_id)
    # # print(channel_id)
    # print(discord_bot.delete_messages_with_keywords_in_channel(channel_id=channel_id))

if __name__ == "__main__":
    main()
