from telethon import TelegramClient

api_id = 123456          # get from https://my.telegram.org
api_hash = "your_api_hash"
channel = -1002480957486 # your channel id

client = TelegramClient("session_name", api_id, api_hash)

async def main():
    async for msg in client.iter_messages(channel, limit=100):
        print(msg.id, msg.date, msg.sender_id, msg.text)

with client:
    client.loop.run_until_complete(main())
