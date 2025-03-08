from datetime import timedelta


DEBUG_MODE = True


# APY tracking
TOP_APY_SUBNETS = 3  # Number of top APY subnets to rotate between

# Price trend settings
PRICE_WINDOW_SHORT = 12  # 1 hour if checking every 5 minutes
PRICE_WINDOW_LONG = 72   # 6 hours if checking every 5 minutes
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# Advanced settings
INTERVAL_MINUTES = 60  # Default interval for checking - will be adjusted dynamically
DIVIDEND_CHECK_INTERVAL = timedelta(seconds=30)
PRICE_CHECK_INTERVAL = timedelta(minutes=5)
VALIDATOR_TRACK_INTERVAL = timedelta(minutes=15)
APY_CHECK_INTERVAL = timedelta(hours=4)

# Thresholds
MIN_ROOT_STAKE = 0.1
MIN_STAKE_THRESHOLD = 0.005
VOLATILITY_THRESHOLD = 0.15  # 15% threshold for high volatility
PRICE_DIP_THRESHOLD = 0.05  # 5% price drop considered a dip
VALIDATOR_ACTIVITY_THRESHOLD = 3  # Number of major validators needed to trigger front-running
APY_ROTATION_THRESHOLD = 0.2  # 20% APY difference to trigger rotation
SUBNET_SATURATION_THRESHOLD = 0.85  # 85% saturation threshold