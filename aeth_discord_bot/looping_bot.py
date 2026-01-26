import sys
import os
import time
from typing import Dict, Optional, Callable, Set

# Add parent directory to path to import constants
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeth_discord_bot.bot import DiscordBot
from aeth_discord_bot.analysis import get_bot_staked_in_subnet
from aeth_discord_bot.analysis import get_subnet_info
from aeth_discord_bot.message_handler import message_handler
from dotenv import load_dotenv

load_dotenv(f"{os.path.dirname(os.path.abspath(__file__))}/bot.env")


class MessageListenerBot(DiscordBot):
    """
    Simple polling-based bot that checks a channel for new messages and replies
    """
    
    def __init__(self):
        super().__init__()
        self.processed_messages: Set[str] = set()
        self.message_handler: Optional[Callable] = None
        self.running = False
        self.bot_user_id = None
    
    def init_seen_message_ids(self, channel_id: str):
        messages = self.fetch_messages(limit=100, channel_id=channel_id)
        for message in messages:
            self.processed_messages.add(message.get("id"))


    def _get_bot_user_id_sync(self) -> Optional[str]:
        """Get the bot's own user ID (synchronous version)"""
        return self._get_bot_user_id()
    
    def set_message_handler(self, handler: Callable[[Dict], Optional[str]]):
        """
        Set a custom message handler function
        
        Args:
            handler: A function that takes a message dict and returns a reply string (or None to not reply)
                    Example: handler(message) -> "Hello!" or None
        """
        self.message_handler = handler
    
    def _handle_message(self, message_data: Dict, channel_id: str):
        """Handle incoming message and reply if needed"""
        message_id = message_data.get("id")
        if not message_id:
            return
        
        # Skip if already processed
        if message_id in self.processed_messages:
            return
        
        # Ignore messages from bots (including ourselves)
        author = message_data.get("author", {})
        if author.get("bot", False):
            self.processed_messages.add(message_id)  # Mark as processed but don't reply
            return
        
        content = message_data.get("content", "")
        author_name = author.get("username", "Unknown")
        author_id = author.get("id")  # Get user ID for mention
        
        print(f"New message from {author_name}: {content[:50]}...")
        
        # Use custom handler if set, otherwise use default reply
        reply_content = None
        if self.message_handler:
            try:
                reply_content = self.message_handler(message_data)
            except Exception as e:
                print(f"Error in message handler: {e}")
        else:
            # Default reply behavior
            reply_content = f"Hello! You said: {content[:100]}"
        
        # Send reply if we have content
        # Note: The handler function should already include the mention if needed
        if reply_content:
            message_id_sent = self.send_message(content=reply_content, channel_id=channel_id)
            if message_id_sent:
                print(f"✓ Replied to {author_name}")
        
        # Mark message as processed
        self.processed_messages.add(message_id)
    
    def start_polling(self, channel_id: str, poll_interval: float = 2.0, reply_content: Optional[str] = None):
        """
        Start polling a channel for new messages and reply automatically
        
        Args:
            channel_id: The Discord channel ID to poll
            poll_interval: How often to check for new messages (in seconds). Default: 2.0
            reply_content: Optional default reply content. If None, uses default reply or custom handler.
        """
        # Get bot user ID to ignore our own messages
        self.bot_user_id = self._get_bot_user_id_sync()
        if not self.bot_user_id:
            print("Warning: Could not get bot user ID. May reply to own messages.")
        
        # Set default reply if provided
        original_handler = None
        if reply_content:
            original_handler = self.message_handler
            self.message_handler = lambda msg: reply_content
        
        print(f"Starting to poll channel {channel_id} every {poll_interval} seconds...")
        print("Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while self.running:
                # Fetch recent messages (most recent first)
                messages = self.fetch_messages(limit=10, channel_id=channel_id)
                
                if messages:
                    # Process messages in reverse order (oldest first) to maintain chronological order
                    for message in reversed(messages):
                        if not self.running:
                            break
                        self._handle_message(message, channel_id)
                
                # Wait before next poll
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            print("\nStopping bot...")
            self.running = False
        finally:
            # Restore original handler if we set a default reply
            if reply_content and original_handler:
                self.message_handler = original_handler
    
    def stop_polling(self):
        """Stop the polling loop"""
        self.running = False


def main():
    """
    Main function to run the message listener bot
    """
    bot = MessageListenerBot()
    
    # Configure your channel ID here
    CHANNEL_ID = "1465038917672894698"  # Replace with your channel ID
    
    # Option 1: Simple reply with a fixed message
    # Uncomment the line below to reply with a fixed message to all messages
    # bot.start_polling(channel_id=CHANNEL_ID, poll_interval=2.0, reply_content="Hello! I received your message!")
    
    # Set the custom handler
    bot.set_message_handler(message_handler)
    
    bot.init_seen_message_ids(channel_id=CHANNEL_ID)
    # Start polling (this will run indefinitely until stopped with Ctrl+C)
    bot.start_polling(channel_id=CHANNEL_ID, poll_interval=1.0)


if __name__ == "__main__":
    main()
