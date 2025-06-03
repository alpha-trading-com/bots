import requests
import json
from twitter_bot.twitter_bot_x import TwitterBotX


WEBHOOK_URL = "https://discord.com/api/webhooks/1379490127151370260/M3gi6L-7pyzl6EoTfc6vUj6SayRyY7tCT0BD2Bv5DK0sm7SUKxdseKzV2GZOjXJkR4CX"

def send_message(content):
    data = {
        "content": content,
        "username": "Webgenie bot",  # Optional: Custom username for the webhook
        "avatar_url": "https://vidaio-justin.s3.us-east-2.amazonaws.com/favicon.ico"  # Optional: Custom avatar for the webhook
    }
    
    response = requests.post(WEBHOOK_URL, data=json.dumps(data), headers={"Content-Type": "application/json"})
    
    if response.status_code == 204:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")

def callback(username, content):
    print(f"Username: {username}")
    print(f"Content: {content}")
    send_message(f"""New tweet from {username}: {content}""")

def main():
    bot = TwitterBotX()
    bot.check_new_tweets(["OpenGradient"], callback)

if __name__ == "__main__":
    main()