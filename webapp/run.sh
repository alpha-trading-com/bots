#!/bin/bash

# Discord Bot Web Interface Run Script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists and activate it
if [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check for required environment variables
if [ -z "$DISCORD_BOT_TOKEN" ]; then
    echo "Warning: DISCORD_BOT_TOKEN environment variable is not set"
    echo "Please set it with: export DISCORD_BOT_TOKEN='Bot YOUR_TOKEN_HERE'"
    echo ""
fi

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "Error: uvicorn is not installed"
    echo "Please install dependencies: pip install -r ../requirements.txt"
    exit 1
fi

# Run the FastAPI application
echo "Starting Discord Bot Web Interface..."
echo "Access the interface at: http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

