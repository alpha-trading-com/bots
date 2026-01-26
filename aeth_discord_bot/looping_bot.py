import sys
import os
import time
from typing import Dict, Optional, Callable, Set

# Add parent directory to path to import constants
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeth_discord_bot.bot import DiscordBot
from aeth_discord_bot.analysis import get_bot_staked_in_subnet
from aeth_discord_bot.analysis import get_subnet_info
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
    
    # Option 2: Custom message handler
    def custom_message_handler(message: Dict) -> Optional[str]:
        """Custom handler that can implement different logic based on message content"""
        # Debug: Print full message to see all fields
        print("=" * 50)
        print("Full message data:")
        import json
        print(json.dumps(message, indent=2))
        print("=" * 50)
        
        # Try to get content from multiple possible locations
        content = message.get("content", "").strip()
        
        # Check if it's an interaction/slash command
        interaction = message.get("interaction", {})
        if interaction:
            # Slash command - try to get command name and options
            command_name = interaction.get("name", "")
            command_data = interaction.get("data", {})
            options = command_data.get("options", [])
            
            # Reconstruct command from interaction data
            if command_name:
                content = f"/{command_name}"
                for opt in options:
                    if "value" in opt:
                        content += f" {opt['value']}"
        
        # If still empty, check for referenced message content
        if not content:
            referenced_message = message.get("referenced_message")
            if referenced_message:
                content = referenced_message.get("content", "").strip()
        
        # If still empty, check message type and other fields
        if not content:
            message_type = message.get("type", 0)
            print(f"Warning: Empty content for message type {message_type}")
            print(f"Message has embeds: {bool(message.get('embeds'))}")
            print(f"Message has attachments: {bool(message.get('attachments'))}")
            print(f"Message has components: {bool(message.get('components'))}")
            # Return None for empty content messages
            return None
        
        content_lower = content.lower()
        author = message.get("author", {})
        author_name = author.get("username", "Unknown")
        
        print(f"Processing content: '{content}'")
        
        # Handle /bots_stake_info command (with or without leading slash)
        if content_lower.startswith("/bots_stake_info") or content_lower.startswith("!bots_stake_info"):
            try:
                # Parse subnet_id from command: /bots_stake_info subnet_id or bots_stake_info subnet_id
                # Remove leading slash if present
                content_clean = content.lstrip("/")
                parts = content_clean.split()
                print(f"Command parts: {parts}")
                if len(parts) < 2:
                    return "❌ Usage: `/bots_stake_info <subnet_id>`\nExample: `/bots_stake_info 2`"
                
                subnet_id = int(parts[1])
                
                # Get bot stake info
                print(f"Fetching bot stake info for subnet {subnet_id}...")
                total_staked, bot_infos = get_bot_staked_in_subnet(subnet_id)
                
                # Format the response
                response = f"**Bot Stake Info for Subnet {subnet_id}**\n\n"
                response += f"**Total Staked:** {total_staked:.2f} TAO\n\n"
                
                if bot_infos:
                    # Sort by staked amount (descending)
                    bot_infos_sorted = sorted(bot_infos, key=lambda x: x["staked_amount"], reverse=True)
                    
                    response += "**Bots (staked ≥ 0.5 TAO):**\n"
                    for bot_info in bot_infos_sorted:
                        bot_addr = bot_info["bot"]
                        staked = bot_info["staked_amount"]
                        # Show shortened address (first 8 chars)
                        bot_short = bot_addr[:8] + "..." + bot_addr[-8:]
                        response += f"• `{bot_short}`: {staked:.2f} TAO\n"
                else:
                    response += "No bots with stake ≥ 0.5 TAO found in this subnet."
                
                return response
                
            except ValueError:
                return "❌ Invalid subnet ID. Please provide a valid number.\nExample: `/bots_stake_info 2`"
            except Exception as e:
                print(f"Error fetching bot stake info: {e}")
                return f"❌ Error fetching bot stake info: {str(e)}"
        elif content_lower.startswith("!subnet"):
            try:
                parts = content.split()
                if len(parts) < 2:
                    return "❌ Usage: `!subnet <subnet_id>`\nExample: `!subnet 2`"
                subnet_id = int(parts[1])
                
                # Fetch subnet info (replace with actual function or logic)
                subnet_info = get_subnet_info(subnet_id)
                if not subnet_info:
                    return f"❌ Subnet ID {subnet_id} not found."
                
                # Compose a nice reply
                response = f"**Subnet Information for ID {subnet_id}**\n\n"
                if "name" in subnet_info:
                    response += f"**Name:** {subnet_info['name']}\n"
                if "price" in subnet_info:
                    response += f"**Price:** {subnet_info['price']} TAO\n"
                if "owner" in subnet_info:
                    owner_short = subnet_info['owner'][:8] + "..." + subnet_info['owner'][-8:]
                    response += f"**Owner:** `{owner_short}`\n"
                if "tao_in" in subnet_info:
                    response += f"**TAO In:** {subnet_info['tao_in']} TAO\n"
                if "alpha_in" in subnet_info:
                    response += f"**Alpha In:** {subnet_info['alpha_in']} Alpha\n"
                if "alpha_out" in subnet_info:
                    response += f"**Alpha Out:** {subnet_info['alpha_out']} Alpha\n"
                if "emission" in subnet_info:
                    response += f"**Emission:** {subnet_info['emission']} TAO\n"
                # Add more fields as needed
                
                return response
                
            except ValueError:
                return "❌ Invalid subnet ID. Please provide a valid number.\nExample: `!subnet 2`"
            except Exception as e:
                print(f"Error fetching subnet info: {e}")
                return f"❌ Error fetching subnet info: {str(e)}"
        # Example: Reply differently based on message content
        elif "hello" in content_lower or "hi" in content_lower:
            return f"Hi {author_name}! How can I help you?"
        elif "help" in content_lower:
            return "I'm here to help! Use `!bots_stake_info <subnet_id>` to get bot stake information. Use `!subnet <subnet_id>` to get subnet information." 
        else:
            return ":joy:"
    
    # Set the custom handler
    bot.set_message_handler(custom_message_handler)
    
    bot.init_seen_message_ids(channel_id=CHANNEL_ID)
    # Start polling (this will run indefinitely until stopped with Ctrl+C)
    bot.start_polling(channel_id=CHANNEL_ID, poll_interval=1.0)


if __name__ == "__main__":
    main()
