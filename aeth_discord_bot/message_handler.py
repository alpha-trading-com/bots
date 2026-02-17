from typing import Dict, Optional
import time
from aeth_discord_bot.analysis import get_bot_staked_in_subnet
from aeth_discord_bot.analysis import get_jeeter_staked_in_subnet
from aeth_discord_bot.analysis import get_subnet_info
from aeth_discord_bot.gateway import get_tao_price, get_btc_price
from aeth_discord_bot.analysis import get_reg_price



HELP_MESSAGE = (
    "Hi <@{author_id}>! I'm here to help!\n\n"
    "- Use `!bots_stake_info <subnet_id>` to get information about bot stakes in a subnet.\n"
    "- Use `!subnet <subnet_id>` for details about a subnet.\n"
    "- Use `!tao_price` to get the current price of TAO.\n"
    "- Use `!reg_price or !burn_cost` to get the current registration price for a subnet.\n"
)

def get_help_message(author_id: str = None, content: str = None) -> str:
    return HELP_MESSAGE.format(author_id=author_id)

def get_exception_message(author_id: str = None, content: str = None) -> str:
    content_lower = content.lower()
    if "58" in content_lower and "who" in content_lower:
        return "DSV bought sn58."

    if "110" in content_lower and "who" in content_lower:
        return "DSV bought sn110."
    
    if "102" in content_lower and "who" in content_lower:
        return "DSV bought sn102."

    if "21" in content_lower and "who" in content_lower:
        return "DSV bought sn21."
    
    if "55" in content_lower and "who" in content_lower:
        return "Yuma still is holding sn55. They might gonna new project on it or might gonna sell it."

    EXCEPTION_MESSAGE = """
    Do your own research rather than asking stupid questions. :joy:
    """
    return EXCEPTION_MESSAGE

def get_hello_message(author_id: str = None, content: str = None) -> str:
    HELLO_MESSAGE = """
    Hi <@{author_id}>! How can I help you?
    """
    return HELLO_MESSAGE.format(author_id=author_id)

def get_bots_stake_info_message(author_id: str = None, content: str = None) -> str:
    # Parse subnet_id from command: /bots_stake_info subnet_id or bots_stake_info subnet_id
    # Remove leading slash if present
    content_clean = content.lstrip("/!")
    parts = content_clean.split()
    print(f"Command parts: {parts}")
    if len(parts) < 2:
        return f"❌ Usage: `/bots_stake_info <subnet_id>`\nExample: `/bots_stake_info 2`"
    
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
            bot_short = bot_addr
            response += f"• `{bot_short}`: {staked:.2f} TAO\n"
    else:
        response += "No bots with stake ≥ 0.5 TAO found in this subnet."
    
    return response
    
def get_jeeters_stake_info_message(author_id: str = None, content: str = None) -> str:
    # Parse subnet_id from command: /jeeters_stake_info subnet_id or jeeters_stake_info subnet_id
    # Remove leading slash if present
    content_clean = content.lstrip("/!")
    parts = content_clean.split()
    print(f"Command parts: {parts}")
    if len(parts) < 2:
        return f"❌ Usage: `/jeeters_stake_info <subnet_id>`\nExample: `/jeeters_stake_info 2`"
    subnet_id = int(parts[1])
    
    # Get jeeter stake info
    print(f"Fetching jeeter stake info for subnet {subnet_id}...")
    total_staked, jeeter_infos = get_jeeter_staked_in_subnet(subnet_id)
    
    # Format the response
    response = f"**Jeeter Stake Info for Subnet {subnet_id}**\n\n"
    response += f"**Total Staked:** {total_staked:.2f} TAO\n\n"
    
    if jeeter_infos:
        # Sort by staked amount (descending)
        jeeter_infos_sorted = sorted(jeeter_infos, key=lambda x: x["staked_amount"], reverse=True)
        
        response += "**Jeeters (staked ≥ 0.5 TAO):**\n"
        for jeeter_info in jeeter_infos_sorted:
            jeeter_addr = jeeter_info["address"]
            jeeter_name = jeeter_info["owner"]
            staked = jeeter_info["staked_amount"]
            # Show shortened address (first 8 chars)
            jeeter_short = jeeter_addr
            response += f"• `{jeeter_short}` ({jeeter_name}): {staked:.2f} TAO\n"
    else:
        response += "No jeeters with stake ≥ 0.5 TAO found in this subnet."
    
    return response

def get_subnet_info_message(author_id: str = None, content: str = None) -> str:
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
        def as_k(val):
            try:
                val = float(val)
                if abs(val) >= 1000:
                    return f"{val/1000:.2f}K"
                else:
                    return f"{val:.2f}"
            except Exception:
                return str(val)
        response = f"**Subnet Information for ID {subnet_id}**\n\n"
        if "name" in subnet_info:
            response += f"**Name:** {subnet_info['name']}\n"
        if "price" in subnet_info:
            response += f"**Price:** {subnet_info['price']} TAO\n"
        if "owner" in subnet_info:
            owner_short = subnet_info['owner']
            response += f"**Owner:** `{owner_short}`\n"
        if "tao_in" in subnet_info:
            response += f"**TAO In:** {as_k(subnet_info['tao_in'])} TAO\n"
        if "alpha_in" in subnet_info:
            response += f"**Alpha In:** {as_k(subnet_info['alpha_in'])} Alpha\n"
        if "alpha_out" in subnet_info:
            response += f"**Alpha Out:** {as_k(subnet_info['alpha_out'])} Alpha\n"
        # if "emission" in subnet_info:
        #     response += f"**Emission:** {round(subnet_info['emission'] * 100)}% TAO\n"
        # Add more fields as needed

        return response
    except ValueError:
        return "❌ Invalid subnet ID. Please provide a valid number.\nExample: `!subnet 2`"
    except Exception as e:
        print(f"Error fetching subnet info: {e}")
        return f"❌ Error fetching subnet info: {str(e)}"

def get_tao_price_message(author_id: str = None, content: str = None) -> str:
    tao_price = get_tao_price()
    btc_price = get_btc_price()
    
    response = "**Current Prices**\n\n"
    
    if tao_price is not None:
        if tao_price >= 1:
            tao_str = f"${tao_price:,.2f}"
        else:
            tao_str = f"${tao_price:.4f}"
        response += f"**TAO:** {tao_str} USD\n"
    else:
        response += "**TAO:** Unable to fetch price\n"
    
    if btc_price is not None:
        btc_str = f"${btc_price:,.2f}"
        response += f"**BTC:** {btc_str} USD\n"
    else:
        response += "**BTC:** Unable to fetch price\n"
    
    return response

def get_reg_price_info_message(author_id: str = None, content: str = None) -> str:
    info = get_reg_price()
    response = "**Subnet Registration Price**\n\n"
    response += f"**Price:** {info['burn_cost']:.2f} TAO\n"
    response += f"**Prune Subnet ID:** {info['prune_subnet_id']}\n"
    subnet_info = get_subnet_info(info['prune_subnet_id'])
    
    response += f"**Subnet ADR:** {subnet_info['ADR']:.2f}\n"
    response += f"**Subnet Price:** {subnet_info['price']:.4f} TAO\n"
    response += f"**Subnet TAO In:** {subnet_info['tao_in']:.2f} TAO\n"
    response += f"**Subnet Alpha In:** {subnet_info['alpha_in']:.2f} Alpha\n"
    response += f"**Subnet Alpha Out:** {subnet_info['alpha_out']:.2f} Alpha\n"
    return response


    # Option 2: Custom message handler
def message_handler(message: Dict, channel_id: str) -> Optional[str]:
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
    author_id = author.get("id")  # Get user ID for mention
    # if author_id == "1225088917733244968":
    #     return "I will ignore you from now on because you insult me.:joy:"

    # if author_id == "1273724526190006467":
    #     time.sleep(1000 * 60 * 2)
    # Handle /bots_stake_info command (with or without leading slash)
    if content_lower.startswith("/bots_stake_info") or content_lower.startswith("!bots_stake_info") or content_lower.startswith("!bots"):
        return get_bots_stake_info_message(author_id, content)
    elif content_lower.startswith("/jeeters_stake_info") or content_lower.startswith("!jeeters_stake_info") or content_lower.startswith("!jeeters"):
        if channel_id != "1465309699229618353":
            return "❌ This command is only available in the #jeeters channel."
        return get_jeeters_stake_info_message(author_id, content)
    elif content_lower.startswith("!reg_price") or content_lower.startswith("!burn_cost"):
        return get_reg_price_info_message(author_id, content)
    elif content_lower.startswith("!subnet"):
        return get_subnet_info_message(author_id, content)
    elif content_lower.startswith("!tao_price"):
        return get_tao_price_message(author_id, content)
    # Example: Reply differently based on message content
    elif "hello" in content_lower or "hi" in content_lower:
        return get_hello_message(author_id, content)
    elif "help" in content_lower:
        return get_help_message(author_id)
    else:
        # Return None to not reply to other messages
        return get_exception_message(author_id, content)
    