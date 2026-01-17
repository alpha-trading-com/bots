import requests
import time
from typing import List, Dict


class DiscordMessageDeleter:
    def __init__(self, bot_token: str, channel_id: str):
        """
        Initialize the message deleter
        
        Args:
            bot_token: Discord bot token (format: "Bot YOUR_TOKEN" or just "YOUR_TOKEN")
            channel_id: Discord channel ID to delete messages from
        """
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.api_base = f"https://discord.com/api/v10/channels/{channel_id}"
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Discord API requests"""
        return {
            "Authorization": self.bot_token,
            "Content-Type": "application/json"
        }
    
    def fetch_messages(self, limit: int = 100, before: str = None) -> List[Dict]:
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
                response = requests.get(f"{self.api_base}/messages", headers=headers, params=params)
                
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
    
    def delete_message(self, message_id: str) -> bool:
        """
        Delete a single message
        
        Args:
            message_id: ID of the message to delete
        
        Returns:
            True if successful, False otherwise
        """
        headers = self.get_headers()
        url = f"{self.api_base}/messages/{message_id}"
        
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
    
    def delete_all_messages(self, batch_delay: float = 0.5):
        """
        Delete all messages in the channel
        
        Args:
            batch_delay: Delay between batches of deletions (in seconds)
        """
        print(f"Starting to delete all messages from channel {self.channel_id}...")
        
        total_deleted = 0
        total_failed = 0
        before = None
        
        while True:
            # Fetch a batch of messages
            messages = self.fetch_messages(limit=100, before=before)
            
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
                author_name = author.get("username", "Unknown")
                content_preview = message.get("content", "")[:50]
                
                if self.delete_message(message_id):
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


def main():
    """
    Main function to run the message deleter
    Configure your bot token and channel ID here
    """
    # Configuration - Replace these with your actual values
    BOT_TOKEN = "your bot token" # Your bot token
    CHANNEL_ID = "your channel id"  # Replace with the channel ID you want to delete messages from
    
    if not CHANNEL_ID:
        print("Error: Please set CHANNEL_ID in the main() function")
        return
    
    # Create deleter instance
    deleter = DiscordMessageDeleter(bot_token=BOT_TOKEN, channel_id=CHANNEL_ID)
    
    # Confirm before deleting
    print(f"WARNING: This will delete ALL messages in channel {CHANNEL_ID}")
    print("Press Ctrl+C to cancel, or wait 5 seconds to continue...")
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        return
    
    # Delete all messages
    deleter.delete_all_messages(batch_delay=0.5)


if __name__ == "__main__":
    main()
