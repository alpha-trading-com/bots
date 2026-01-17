from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import sys
import os

# Add parent directory to path to import DiscordBot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aeth_discord_bot.bot import DiscordBot

app = FastAPI(title="Discord Bot Web Interface")

# Initialize DiscordBot (you'll need to set BOT_TOKEN as environment variable)
BOT_TOKEN = "Bot MTQ2MTc5MTY5Njc2NDI3Njg1OQ.GIhtn-.6Leg1a-SYNgQ0AJbXegFEiyJnr2Zy9OmA38qvM"
GUILD_ID = "1420796398307377284"  # Hardcoded guild ID

discord_bot = DiscordBot(bot_token=BOT_TOKEN)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Pydantic models for request/response
class SendMessageRequest(BaseModel):
    content: str
    channel_id: str


class SendDMRequest(BaseModel):
    content: str
    user_id: str


class DeleteMessageRequest(BaseModel):
    message_id: str
    channel_id: str


# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    html_path = os.path.join(STATIC_DIR, "index.html")
    with open(html_path, "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/guild/members")
async def get_guild_members():
    """Get all members from a guild"""
    try:
        members = discord_bot.get_all_guild_members(guild_id=GUILD_ID)
        return {"members": members}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/guild/channels")
async def get_guild_channels():
    """Get all channels from a guild"""
    try:
        channels = _get_guild_channels(GUILD_ID)
        # Filter to only text channels (type 0) and announcement channels (type 5)
        text_channels = [
            ch for ch in channels 
            if ch.get("type") in [0, 5]
        ]
        return {"channels": text_channels}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_guild_channels(guild_id: str) -> List[Dict]:
    """Helper function to get guild channels"""
    import requests
    headers = discord_bot.get_headers()
    url = f"{discord_bot.api_base}/guilds/{guild_id}/channels"
    
    retries = 5
    while retries > 0:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                import time
                retry_after = float(response.headers.get("Retry-After", 1))
                time.sleep(retry_after)
                continue
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
        except Exception as e:
            retries -= 1
            if retries == 0:
                raise
            import time
            time.sleep(2)
    
    return []



@app.get("/api/dm/channel/{user_id}")
async def get_dm_channel(user_id: str):
    """Get or create DM channel with a user"""
    try:
        dm_channel_id = discord_bot._get_dm_channel_id(user_id=user_id)
        if not dm_channel_id:
            raise HTTPException(status_code=404, detail="Failed to get DM channel")
        return {"channel_id": dm_channel_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dm/messages/{user_id}")
async def get_dm_messages(user_id: str, limit: int = 100):
    """Get all messages in a DM with a user (including bot messages)"""
    try:
        dm_channel_id = discord_bot._get_dm_channel_id(user_id=user_id)
        if not dm_channel_id:
            raise HTTPException(status_code=404, detail="Failed to get DM channel")
        
        messages = discord_bot.fetch_messages(limit=limit, channel_id=dm_channel_id)
        # Get bot user ID to mark bot messages
        bot_user_id = discord_bot._get_bot_user_id()
        
        # Format messages for frontend
        formatted_messages = []
        for msg in messages:
            author = msg.get("author", {})
            formatted_messages.append({
                "id": msg.get("id"),
                "content": msg.get("content", ""),
                "author_id": author.get("id"),
                "author_name": author.get("username", "Unknown"),
                "timestamp": msg.get("timestamp"),
                "is_bot": author.get("id") == bot_user_id
            })
        
        return {"messages": formatted_messages, "channel_id": dm_channel_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/channel/messages/{channel_id}")
async def get_channel_messages(channel_id: str, limit: int = 100):
    """Get messages from a channel"""
    try:
        messages = discord_bot.fetch_messages(limit=limit, channel_id=channel_id)
        bot_user_id = discord_bot._get_bot_user_id()
        
        # Format messages for frontend
        formatted_messages = []
        for msg in messages:
            author = msg.get("author", {})
            formatted_messages.append({
                "id": msg.get("id"),
                "content": msg.get("content", ""),
                "author_id": author.get("id"),
                "author_name": author.get("username", "Unknown"),
                "timestamp": msg.get("timestamp"),
                "is_bot": author.get("id") == bot_user_id
            })
        
        return {"messages": formatted_messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dm/send")
async def send_dm(request: SendDMRequest):
    """Send a DM to a user"""
    try:
        message_id = discord_bot.send_dm(
            user_id=request.user_id,
            content=request.content
        )
        if not message_id:
            raise HTTPException(status_code=500, detail="Failed to send DM")
        return {"message_id": message_id, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/channel/send")
async def send_channel_message(request: SendMessageRequest):
    """Send a message to a channel"""
    try:
        message_id = discord_bot.send_message(
            content=request.content,
            channel_id=request.channel_id
        )
        if not message_id:
            raise HTTPException(status_code=500, detail="Failed to send message")
        return {"message_id": message_id, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/message/delete")
async def delete_message(
    message_id: str = Query(..., description="Message ID to delete"),
    channel_id: str = Query(..., description="Channel ID where the message is")
):
    """Delete a message"""
    try:
        success = discord_bot.delete_message(
            message_id=message_id,
            channel_id=channel_id
        )
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/channel/clear")
async def clear_channel(user_id: str):
    """Clear all messages in a channel"""
    try:
        success = discord_bot.clears(user_id=user_id)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

