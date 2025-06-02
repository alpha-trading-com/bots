import os
import tweepy
from dotenv import load_dotenv
from datetime import datetime

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

    def get_user_id(self, username):
        """Get user ID from username"""
        try:
            user = self.client.get_user(username=username)
            return user.data.id
        except Exception as e:
            print(f"Error getting user ID: {e}")
            return None

    def get_recent_tweets(self, username, max_results=10):
        """Get recent tweets from a specified user"""
        try:
            user_id = self.get_user_id(username)
            if not user_id:
                return None

            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics']
            )

            if not tweets.data:
                print(f"No tweets found for user: {username}")
                return None

            formatted_tweets = []
            for tweet in tweets.data:
                tweet_data = {
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

def main():
    # Initialize the bot
    bot = TwitterBot()

    # Example usage
    username = "OpenGradient"
    max_tweets = 10

    tweets = bot.get_recent_tweets(username, min(max_tweets, 100))
    
    if tweets:
        print(f"\nRecent tweets from @{username}:")
        print("-" * 50)
        for tweet in tweets:
            print(f"\nTweet: {tweet['text']}")
            print(f"Posted at: {tweet['created_at']}")
            print("-" * 50)

if __name__ == "__main__":
    main() 