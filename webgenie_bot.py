import os
import requests
import json
from constants import USERS, WEBHOOK_URL
from twitter_bot.twitter_bot_x import TwitterBotX
import time
import threading


TWEETS_DIR = "tweets"


def make_tweet_dir():
    if not os.path.exists(TWEETS_DIR):
        os.makedirs(TWEETS_DIR)


def send_message(content):
    data = {
        "content": content,
        "username": "Webgenie bot",  # Optional: Custom username for the webhook
        "avatar_url": "https://vidaio-justin.s3.us-east-2.amazonaws.com/favicon.ico"  # Optional: Custom avatar for the webhook
    }
    response = requests.post(WEBHOOK_URL, data=json.dumps(data), headers={"Content-Type": "application/json"})
    
    if response.status_code == 204:
        print("Message sent successfully!")
        return True
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")
    return False


def format_tweet(tweet):
    # Format the timestamp
    created_at = tweet['created_at']
    # Create a beautiful formatted message
    message = f"""🐦 **New Tweet Alert from {tweet['username']}!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 **Author:** {tweet['username']}
⏰ **Time:** {created_at}
💬 **Content:**
{tweet['text']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 **Link:** https://x.com/{tweet['username']}/status/{tweet['id']}


"""  
    return message


def periodic_check(interval=5):
    while True:
        for tweet_file_name in os.listdir(TWEETS_DIR):
            with open(f"{TWEETS_DIR}/{tweet_file_name}", 'r') as f:
                tweet = json.load(f)
                message = format_tweet(tweet)   
                result = send_message(message)
                if result:
                    os.remove(f"{TWEETS_DIR}/{tweet_file_name}")
        time.sleep(interval)


def callback(tweet):
    try:
        filename = f"{TWEETS_DIR}/{tweet['id']}.json"
        with open(filename, 'w') as f:
            json.dump(tweet, f, indent=4, default=str)
        print(f"Saved tweet {tweet['id']} to {filename}")
    except Exception as e:
        print(f"Error saving tweet {tweet['id']}: {e}")


def run_periodic_check():
    make_tweet_dir()
    check_thread = threading.Thread(target=periodic_check)
    check_thread.daemon = True
    check_thread.start()


def main():
    run_periodic_check()
    bot = TwitterBotX()
    usernames = USERS
    bot.check_new_tweets(usernames, callback)


if __name__ == "__main__":
    main()