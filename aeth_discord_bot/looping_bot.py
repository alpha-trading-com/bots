import sys
import os
import time
from typing import Dict, Optional, Callable, Set, Union, List

# Add parent directory to path to import constants
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeth_discord_bot.bot import DiscordBot
from aeth_discord_bot.analysis import get_bot_staked_in_subnet
from aeth_discord_bot.analysis import get_subnet_info
from aeth_discord_bot.message_handler import message_handler
from aeth_discord_bot.gateway import DiscordGateway
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
        self.gateway: Optional[DiscordGateway] = None
    
    def init_seen_message_ids(self, channel_id: Union[str, List[str]]):
        """
        Initialize seen message IDs for one or more channels
        
        Args:
            channel_id: Single channel ID (str) or list of channel IDs
        """
        channel_ids = [channel_id] if isinstance(channel_id, str) else channel_id
        for ch_id in channel_ids:
            messages = self.fetch_messages(limit=100, channel_id=ch_id)
            for message in messages:
                self.processed_messages.add(message.get("id"))
            print(f"Initialized {len(messages)} seen messages for channel {ch_id}")


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
    
    def start_polling(self, channel_id: Union[str, List[str]], poll_interval: float = 2.0, reply_content: Optional[str] = None, status_message: Optional[str] = None):
        """
        Start polling one or more channels for new messages and reply automatically
        
        Args:
            channel_id: The Discord channel ID(s) to poll. Can be a single channel ID (str) or a list of channel IDs
            poll_interval: How often to check for new messages (in seconds). Default: 2.0
            reply_content: Optional default reply content. If None, uses default reply or custom handler.
            status_message: Optional status message to display (e.g., "Monitoring channels"). If None, uses default.
        """
        # Normalize to list format
        channel_ids = [channel_id] if isinstance(channel_id, str) else channel_id
        
        if not channel_ids:
            print("Error: No channel IDs provided")
            return
        
        # Get bot user ID to ignore our own messages
        self.bot_user_id = self._get_bot_user_id_sync()
        if not self.bot_user_id:
            print("Warning: Could not get bot user ID. May reply to own messages.")
        
        # Start Gateway connection for online status
        bot_token = os.getenv("BOT_TOKEN")
        if bot_token:
            # Remove "Bot " prefix if present (Gateway expects just the token)
            if bot_token.startswith("Bot "):
                bot_token = bot_token[4:]
            default_status = status_message or f"Monitoring {len(channel_ids)} channel{'s' if len(channel_ids) > 1 else ''}"
            # Enable TAO price display in status
            self.gateway = DiscordGateway(bot_token=bot_token, update_price_interval=60)  # Update every 60 seconds
            self.gateway.start(
                status_message=default_status, 
                activity_type=3,  # activity_type 3 = Watching
                show_tao_price=True  # Enable real-time TAO price in status
            )
        else:
            print("Warning: BOT_TOKEN not found. Gateway connection (online status) will not work.")
        
        # Set default reply if provided
        original_handler = None
        if reply_content:
            original_handler = self.message_handler
            self.message_handler = lambda msg: reply_content
        
        if len(channel_ids) == 1:
            print(f"Starting to poll channel {channel_ids[0]} every {poll_interval} seconds...")
        else:
            print(f"Starting to poll {len(channel_ids)} channels every {poll_interval} seconds...")
            print(f"Channels: {', '.join(channel_ids)}")
        print("Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while self.running:
                # Poll each channel
                for ch_id in channel_ids:
                    if not self.running:
                        break
                    
                    # Fetch recent messages (most recent first)
                    messages = self.fetch_messages(limit=10, channel_id=ch_id)
                    
                    if messages:
                        # Process messages in reverse order (oldest first) to maintain chronological order
                        for message in reversed(messages):
                            if not self.running:
                                break
                            self._handle_message(message, ch_id)
                
                # Wait before next poll cycle
                time.sleep(poll_interval)
                
        except KeyboardInterrupt:
            print("\nStopping bot...")
            self.running = False
        finally:
            # Stop Gateway connection
            if self.gateway:
                self.gateway.stop()
            
            # Restore original handler if we set a default reply
            if reply_content and original_handler:
                self.message_handler = original_handler
    
    def stop_polling(self):
        """Stop the polling loop"""
        self.running = False
        if self.gateway:
            self.gateway.stop()


def main():
    """
    Main function to run the message listener bot
    """
    bot = MessageListenerBot()
    
    # Configure your channel ID(s) here
    # Option 1: Single channel (backward compatible)
    # CHANNEL_ID = "1465038917672894698"  # Replace with your channel ID
    
    # Option 2: Multiple channels
    CHANNEL_IDS = [
        "1465038917672894698",  # Channel 1
        "1465309699229618353",  # Channel 2
    ]
    
    # Option 1: Simple reply with a fixed message
    # Uncomment the line below to reply with a fixed message to all messages
    # bot.start_polling(channel_id=CHANNEL_ID, poll_interval=2.0, reply_content="Hello! I received your message!")
    
    # Set the custom handler
    bot.set_message_handler(message_handler)
    
    # Initialize seen messages for all channels
    bot.init_seen_message_ids(channel_id=CHANNEL_IDS)
    # For multiple channels, use:
    # bot.init_seen_message_ids(channel_id=CHANNEL_IDS)
    
    # Start polling (this will run indefinitely until stopped with Ctrl+C)
    # Single channel:
    bot.start_polling(channel_id=CHANNEL_IDS, poll_interval=1.0)
    # Multiple channels:
    # bot.start_polling(channel_id=CHANNEL_IDS, poll_interval=1.0)


if __name__ == "__main__":
    main()
