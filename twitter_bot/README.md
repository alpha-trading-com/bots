# Twitter Bot

A simple Python bot that fetches recent tweets from a specified Twitter account.

## Setup

1. First, you'll need to create a Twitter Developer account and get API credentials:
   - Go to https://developer.twitter.com/
   - Create a new project and app
   - Get your API keys and tokens

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project directory with your Twitter API credentials:
   ```
   TWITTER_API_KEY=your_api_key_here
   TWITTER_API_SECRET=your_api_secret_here
   TWITTER_ACCESS_TOKEN=your_access_token_here
   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
   TWITTER_BEARER_TOKEN=your_bearer_token_here
   ```

## Usage

Run the bot using:
```bash
python twitter_bot.py
```

The script will prompt you to:
1. Enter a Twitter username (without the @ symbol)
2. Specify how many recent tweets you want to fetch (maximum 100)

The bot will then display the tweets along with their creation time, like count, and retweet count.

## Features

- Fetches recent tweets from any public Twitter account
- Displays tweet text, creation time, likes, and retweets
- Error handling for invalid usernames or API issues
- Configurable number of tweets to fetch (up to 100)

## Note

Make sure to keep your API credentials secure and never commit them to version control. 