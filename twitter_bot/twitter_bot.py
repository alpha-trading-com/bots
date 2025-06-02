import os
import tweepy
from dotenv import load_dotenv
from datetime import datetime
import re
import json
import time

# Load environment variables
load_dotenv()

class TwitterBot:
    def __init__(self):
        # Twitter API credentials
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        # Initialize the client
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )
        
        # Load last seen timestamp
        self.last_seen_file = 'last_seen.json'
        self.last_seen = self.load_last_seen()

    def load_last_seen(self):
        """Load the last seen timestamp from file"""
        try:
            if os.path.exists(self.last_seen_file):
                with open(self.last_seen_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading last seen data: {e}")
            return {}

    def save_last_seen(self):
        """Save the last seen timestamp to file"""
        try:
            with open(self.last_seen_file, 'w') as f:
                json.dump(self.last_seen, f)
        except Exception as e:
            print(f"Error saving last seen data: {e}")

    def get_user_id(self, username):
        """Get user ID from username"""
        try:
            user = self.client.get_user(username=username)
            return user.data.id
        except Exception as e:
            print(f"Error getting user ID: {e}")
            return None

    def analyze_content(self, text) -> tuple[bool, int]:
        """Analyze content and count specific words"""
        # Convert text to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Define words to search for
        words_to_count = ['subnet', 'bittensor']  
        # Count occurrences
        word_counts = {}
        for word in words_to_count:
            # Use word boundaries to ensure we're matching whole words
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            count = len(re.findall(pattern, text_lower))
            word_counts[word] = count

        if word_counts['subnet'] > 0 or word_counts['bittensor'] > 0:
            print("Subnet or Bittensor found in tweet")
            subnets = ['54', '69', '47', '78', '82']
            for subnet in subnets:
                if subnet in text_lower:
                    print(f"Subnet {subnet} found in tweet")
                    return True, int(subnet)
            return True, 0
        else:
            return False, 0
        

    def get_recent_tweets(self, username, max_results=10, since_id=None):
        """Get recent tweets from a specified user"""
        try:
            user_id = self.get_user_id(username)
            if not user_id:
                return None

            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics'],
                since_id=since_id
            )

            if not tweets.data:
                print(f"No tweets found for user: {username}")
                return None

            formatted_tweets = []
            for tweet in tweets.data:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'likes': tweet.public_metrics['like_count'],
                    'retweets': tweet.public_metrics['retweet_count']
                }
                formatted_tweets.append(tweet_data)

            return formatted_tweets

        except Exception as e:
            print(f"Error fetching tweets: {e}")
            return None

    def check_new_tweets(self, username, callback, interval=60):
        """Check for new tweets periodically"""
        while True:
            try:
                # Get the last seen tweet ID for this user
                last_id = self.last_seen.get(username)
                
                # Fetch new tweets
                new_tweets = self.get_recent_tweets(username, max_results=5, since_id=last_id)
                
                if new_tweets:
                    # Update last seen ID
                    self.last_seen[username] = new_tweets[0]['id']
                    self.save_last_seen()
                    
                    # Process new tweets
                    tweet = new_tweets[0]
                    content = tweet['text']
                    found, subnet = self.analyze_content(content)

                    if found:
                        print(f"Found {found} in tweet")
                        print(f"Tweet: {content}")

                    if subnet > 0:
                        print(f"Found subnet {subnet} in tweet")
                        print(f"Tweet: {content}")
                        callback(subnet)                        
                    

            except Exception as e:
                print(f"Error in check_new_tweets: {e}")
            time.sleep(interval)



def callback(subnet):
    print(f"Subnet {subnet} found in tweet")

def main():
    # Initialize the bot
    bot = TwitterBot()

    # Example usage
    username = "OpenGradient"

    # Start checking for new tweets
    print(f"Starting to monitor tweets from @{username}...")
    bot.check_new_tweets(username, callback)

if __name__ == "__main__":
    main() 