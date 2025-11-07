#!/bin/bash
# Setup script for SMS News Service
# Automates virtual environment creation and dependency installation

set -e  # Exit on error

echo "=========================================="
echo "SMS News Service - Setup"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Found: $PYTHON_VERSION"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
pip install -r requirements.txt

echo "✓ Dependencies installed"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys and credentials"
else
    echo "✓ .env file already exists"
fi
echo ""

# Check if subscribers.json exists
if [ ! -f "subscribers.json" ]; then
    echo "Creating subscribers.json from template..."
    cp subscribers.json.example subscribers.json
    echo "✓ subscribers.json created"
    echo ""
    echo "⚠️  IMPORTANT: Edit subscribers.json and add your subscriber phone numbers"
else
    echo "✓ subscribers.json already exists"
fi
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys:"
echo "   - TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER"
echo "   - GEMINI_API_KEY or CLAUDE_API_KEY"
echo ""
echo "2. Edit subscribers.json and add subscriber phone numbers"
echo ""
echo "3. Test the service:"
echo "   source venv/bin/activate"
echo "   python3 send_daily_news.py --test"
echo ""
echo "4. To activate the virtual environment in the future:"
echo "   source venv/bin/activate"
echo ""
