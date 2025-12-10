import requests
import time
from typing import List, Dict

def send_webhook_message(
    webhook_url: str, 
    content: str,
    embeds: List[Dict] = [], 
    username: str = "Message Monitor",
    avatar_url: str = "https://cdn.discordapp.com/embed/avatars/0.png"
):
    """Send message to webhook"""

    payload = {
        "content": content,
        "embeds": embeds,
        "username": username,
        "avatar_url": avatar_url
    }
    
    retries = 5
    while retries > 0:
        try:
            response = requests.post(webhook_url, json=payload)
            if response.status_code in [200, 204]:
                print(f"Successfully sent message(s) to webhook")
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


def create_embed(message: Dict, channel_id: str, title: str, color: int = 0xffff00) -> Dict:
    """Create Discord embed from message data"""
    author = message.get("author", {})
    content = message.get("content", "")
    timestamp = message.get("timestamp", "")
    message_id = message.get("id", "")
    
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
                "value": f"<#{channel_id}>",
                "inline": True
            }
        ]
    }
    return embed