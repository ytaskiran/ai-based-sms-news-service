#!/bin/bash
# Convenience script to run the SMS News Service
# Automatically activates virtual environment

set -e  # Exit on error

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Run ./setup.sh first to create the environment"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run the script with all passed arguments
python3 send_daily_news.py "$@"
