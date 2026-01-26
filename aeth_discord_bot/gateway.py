import asyncio
import json
import os
import sys
import threading
import time
from typing import Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import aiohttp
    import zlib
except ImportError:
    print("Warning: aiohttp or zlib not available. Gateway features will be disabled.")
    aiohttp = None
    zlib = None

from dotenv import load_dotenv

load_dotenv(f"{os.path.dirname(os.path.abspath(__file__))}/bot.env")


def get_tao_price() -> Optional[float]:
    """
    Fetch TAO price in USD from CoinGecko API
    
    Returns:
        TAO price in USD, or None if fetch fails
    """
    try:
        import requests
        # CoinGecko API endpoint for Bittensor (TAO)
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bittensor",
            "vs_currencies": "usd"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("bittensor", {}).get("usd")
        else:
            print(f"Failed to fetch TAO price: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching TAO price: {e}")
        return None


class DiscordGateway:
    """
    Minimal Discord Gateway connection for setting bot presence/status.
    This runs in a separate thread to maintain a WebSocket connection.
    """
    
    def __init__(self, bot_token: str, update_price_interval: int = 60):
        self.bot_token = bot_token
        self.ws = None
        self.session = None
        self.running = False
        self.thread = None
        self.sequence = None
        self.session_id = None
        self.gateway_url = None
        self.heartbeat_interval = None
        self.loop = None
        self.decompressor = None  # For zlib-stream decompression
        self.update_price_interval = update_price_interval  # Update price every N seconds
        self.show_tao_price = False  # Whether to show TAO price in status
        
    def start(self, status_message: str = "Monitoring channels", activity_type: int = 3, show_tao_price: bool = False):
        """
        Start the Gateway connection in a background thread
        
        Args:
            status_message: The status message to display (e.g., "Watching for messages")
            activity_type: Activity type (0=Playing, 1=Streaming, 2=Listening, 3=Watching, 4=Custom, 5=Competing)
            show_tao_price: If True, will update status with TAO price periodically
        """
        if aiohttp is None:
            print("Warning: aiohttp not available. Cannot start Gateway connection.")
            return False
            
        if self.running:
            print("Gateway connection already running")
            return False
            
        self.status_message = status_message
        self.activity_type = activity_type
        self.show_tao_price = show_tao_price
        self.running = True
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        print("Gateway connection thread started")
        return True
    
    def stop(self):
        """Stop the Gateway connection"""
        self.running = False
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._close_connection(), self.loop)
        if self.thread:
            self.thread.join(timeout=5)
        print("Gateway connection stopped")
    
    def _run_async_loop(self):
        """Run the async event loop in a separate thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._connect())
        except Exception as e:
            print(f"Gateway connection error: {e}")
        finally:
            self.loop.close()
    
    async def _get_gateway_url(self):
        """Get the Gateway WebSocket URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://discord.com/api/v10/gateway",
                headers={"Authorization": f"Bot {self.bot_token}"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("url")
                else:
                    print(f"Failed to get gateway URL: {resp.status}")
                    return None
    
    async def _connect(self):
        """Connect to Discord Gateway and maintain connection"""
        if not self.gateway_url:
            self.gateway_url = await self._get_gateway_url()
            if not self.gateway_url:
                print("Failed to get gateway URL")
                return
        
        # Add encoding and version to URL
        gateway_ws_url = f"{self.gateway_url}?v=10&encoding=json&compress=zlib-stream"
        
        self.session = aiohttp.ClientSession()
        
        while self.running:
            try:
                async with self.session.ws_connect(gateway_ws_url) as ws:
                    self.ws = ws
                    print("Connected to Discord Gateway")
                    # Initialize decompressor for zlib-stream
                    self.decompressor = zlib.decompressobj() if zlib else None
                    
                    # Handle messages
                    async for msg in ws:
                        if not self.running:
                            break
                            
                        if msg.type == aiohttp.WSMsgType.BINARY:
                            # Handle compressed binary data
                            await self._handle_binary_message(msg.data)
                        elif msg.type == aiohttp.WSMsgType.TEXT:
                            # Handle uncompressed text (shouldn't happen with zlib-stream, but handle it)
                            await self._handle_message(msg.data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"WebSocket error: {ws.exception()}")
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSE:
                            print(f"WebSocket closed: {msg.data}")
                            break
                            
            except Exception as e:
                print(f"Gateway connection error: {e}")
                if self.running:
                    print("Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    break
        
        if self.session:
            await self.session.close()
    
    async def _handle_binary_message(self, data: bytes):
        """Handle binary message from Gateway (zlib-stream compressed)"""
        if not self.decompressor:
            print("Warning: No decompressor available")
            return
            
        try:
            # Decompress the data chunk
            # The decompressor maintains state across chunks
            decompressed = self.decompressor.decompress(data)
            
            if decompressed:
                # Discord sends JSON messages separated by newlines or as complete JSON
                # Try to decode and split by newlines
                try:
                    text = decompressed.decode('utf-8')
                    # Split by newlines in case multiple messages are in one chunk
                    for line in text.strip().split('\n'):
                        if line.strip():
                            await self._handle_message(line.strip())
                except UnicodeDecodeError:
                    # Partial UTF-8 sequence, will be completed in next chunk
                    pass
        except zlib.error as e:
            # zlib error - might need to reset decompressor
            print(f"zlib decompression error: {e}, resetting decompressor")
            self.decompressor = zlib.decompressobj() if zlib else None
        except Exception as e:
            print(f"Error handling binary message: {e}")
    
    async def _handle_message(self, data_str: str):
        """Handle incoming Gateway messages"""
        try:
            data = json.loads(data_str)
            op = data.get("op")
            event = data.get("t")
            payload = data.get("d", {})
            
            if op == 10:  # Hello - contains heartbeat interval
                self.heartbeat_interval = payload.get("heartbeat_interval", 41250) / 1000
                self.sequence = data.get("s")
                
                # Send Identify
                await self._send_identify()
                
                # Start heartbeat
                asyncio.create_task(self._heartbeat_loop())
                
            elif op == 11:  # Heartbeat ACK
                pass
                
            elif op == 0:  # Dispatch event
                self.sequence = data.get("s")
                
                if event == "READY":
                    print("Gateway READY - Bot is now online!")
                    self.session_id = payload.get("session_id")
                    # Set presence after ready
                    await self._update_presence()
                    # Start price update loop if enabled
                    if self.show_tao_price:
                        asyncio.create_task(self._price_update_loop())
                    
                elif event == "RESUMED":
                    print("Gateway RESUMED")
                    await self._update_presence()
                    # Start price update loop if enabled
                    if self.show_tao_price:
                        asyncio.create_task(self._price_update_loop())
                    
            elif op == 7:  # Reconnect
                print("Gateway requested reconnect")
                await self._send_resume()
                
            elif op == 9:  # Invalid session
                print("Invalid session, re-identifying...")
                await asyncio.sleep(5)
                await self._send_identify()
                
        except json.JSONDecodeError:
            # Handle multiple JSON objects in one message
            for line in data_str.strip().split('\n'):
                if line:
                    await self._handle_message(line)
        except Exception as e:
            print(f"Error handling Gateway message: {e}")
    
    async def _send_identify(self):
        """Send Identify payload"""
        payload = {
            "op": 2,
            "d": {
                "token": self.bot_token,
                "properties": {
                    "$os": "linux",
                    "$browser": "aeth_bot",
                    "$device": "aeth_bot"
                },
                "intents": 0  # No intents needed for presence only
            }
        }
        await self._send(payload)
    
    async def _send_resume(self):
        """Send Resume payload"""
        if not self.session_id:
            await self._send_identify()
            return
            
        payload = {
            "op": 6,
            "d": {
                "token": self.bot_token,
                "session_id": self.session_id,
                "seq": self.sequence
            }
        }
        await self._send(payload)
    
    async def _update_presence(self):
        """Update bot presence/status"""
        payload = {
            "op": 3,
            "d": {
                "since": None,
                "activities": [{
                    "name": self.status_message,
                    "type": self.activity_type
                }],
                "status": "online",
                "afk": False
            }
        }
        await self._send(payload)
        print(f"Presence updated: {self.status_message}")
    
    def update_status(self, status_message: str, activity_type: int = 3):
        """
        Update the bot's status message
        
        Args:
            status_message: The new status message to display
            activity_type: Activity type (0=Playing, 1=Streaming, 2=Listening, 3=Watching, 4=Custom, 5=Competing)
        """
        self.status_message = status_message
        self.activity_type = activity_type
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._update_presence(), self.loop)
    
    async def _send(self, payload: dict):
        """Send payload to Gateway"""
        if self.ws and not self.ws.closed:
            try:
                await self.ws.send_str(json.dumps(payload))
            except Exception as e:
                print(f"Error sending Gateway payload: {e}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if self.ws and not self.ws.closed:
                    payload = {
                        "op": 1,
                        "d": self.sequence
                    }
                    await self._send(payload)
            except Exception as e:
                print(f"Heartbeat error: {e}")
                break
    
    async def _close_connection(self):
        """Close the WebSocket connection"""
        if self.ws and not self.ws.closed:
            await self.ws.close()
    
    async def _price_update_loop(self):
        """Periodically update status with TAO price"""
        # Fetch price immediately on first run
        first_run = True
        
        while self.running:
            try:
                if not first_run:
                    await asyncio.sleep(self.update_price_interval)
                else:
                    first_run = False
                    
                if not self.running:
                    break
                    
                tao_price = get_tao_price()
                if tao_price is not None:
                    # Format price nicely
                    if tao_price >= 1:
                        price_str = f"${tao_price:,.2f}"
                    else:
                        price_str = f"${tao_price:.4f}"
                    
                    # Update status with TAO price
                    status_msg = f"TAO: {price_str}"
                    self.status_message = status_msg
                    await self._update_presence()
                    print(f"Updated status with TAO price: {status_msg}")
                else:
                    print("Failed to fetch TAO price, keeping current status")
            except Exception as e:
                print(f"Error in price update loop: {e}")
                # Continue loop even on error
                if not first_run:
                    await asyncio.sleep(self.update_price_interval)
                continue

