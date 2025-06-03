import os
import tweepy
from dotenv import load_dotenv
from datetime import datetime
import re
import json
import time

# Load environment variables
load_dotenv()

class TwitterBotX:
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
        self.last_seen_file = 'last_seen_x.json'
        self.last_seen_id = self.load_last_seen()

    def load_last_seen(self):
        """Load the last seen tweet ID from file"""
        try:
            if os.path.exists(self.last_seen_file):
                with open(self.last_seen_file, 'r') as f:
                    return f.read().strip()
            return None
        except Exception as e:
            print(f"Error loading last seen data: {e}")
            return None

    def save_last_seen(self, tweet_id):
        """Save the last seen tweet ID to file"""
        try:
            with open(self.last_seen_file, 'w') as f:
                f.write(str(tweet_id))
        except Exception as e:
            print(f"Error saving last seen data: {e}")

    def get_tweets_from_multiple_users(self, usernames, max_results=50, since_id=None):
        """Get tweets from multiple users using search_recent_tweets"""
        try:
            # Create a query string with OR operator between usernames
            query = " OR ".join([f"from:{username}" for username in usernames])
            query = f"({query}) -is:retweet -is:reply"
            
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                user_fields=['username', 'name'],
                expansions=['author_id'],
                since_id=since_id
            )
            
            if not tweets.data:
                print(f"No tweets found for users: {usernames}")
                return None
                
            # Process the tweets
            formatted_tweets = []
            for tweet in tweets.data:
                # Get the author's username from the includes
                author = next(user for user in tweets.includes['users'] 
                            if user.id == tweet.author_id)
                
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'username': author.username,
                    'likes': tweet.public_metrics['like_count'],
                    'retweets': tweet.public_metrics['retweet_count']
                }
                formatted_tweets.append(tweet_data)
                
            return formatted_tweets
            
        except Exception as e:
            print(f"Error fetching tweets: {e}")
            return None

    def check_new_tweets(self, usernames, callback, interval=172):
        """Check for new tweets periodically from multiple users"""
        while True:
            try:
                # Get the last seen tweet ID
                since_id = self.last_seen_id
                
                # Fetch new tweets for all users
                new_tweets = self.get_tweets_from_multiple_users(usernames, max_results=50, since_id=since_id)
                
                if new_tweets:
                    # Update last seen ID with the most recent tweet
                    self.last_seen_id = new_tweets[0]['id']
                    self.save_last_seen(self.last_seen_id)
                    
                    # Process new tweets
                    for tweet in new_tweets:
                        username = tweet['username']
                        callback(username, tweet['text'])
                    
            except Exception as e:
                print(f"Error in check_new_tweets: {e}")
            time.sleep(interval)


def callback(username , content):
    print(f"Username: {username}")
    print(f"Content: {content}")


def main():
    # Initialize the bot
    bot = TwitterBotX()

    # List of usernames to monitor
    usernames = ["OpenGradient", "User2", "User3"]  # Add your target usernames here
    
    # Start checking for new tweets
    print(f"Starting to monitor tweets from {usernames}...")
    bot.check_new_tweets(usernames, callback)

if __name__ == "__main__":
    main() 