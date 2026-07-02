#!/bin/bash
# OpenClaw Agent Setup Script

echo "=== OpenClaw Agent Setup ==="

# 1. Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 2. Check Python
echo "Checking system python..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed."
    exit 1
fi

# 2. Setup Virtual Environment
echo "Setting up Python virtual environment (venv)..."
python3 -m venv venv
source venv/bin/activate

# 3. Install Python Dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install requests pyTelegramBotAPI python-dotenv notebooklm-py playwright

# 4. Install Playwright Browser Binaries
echo "Installing Playwright Chromium browser..."
python3 -m playwright install chromium

# 5. Check and Install context7 (Requires Node.js)
if command -v npm &> /dev/null; then
    echo "Node.js detected. Installing context7 globally..."
    sudo npm install -g context7 || echo "Warning: global npm install failed. Try running: npm install -g context7 manually."
else
    echo "Warning: npm/Node.js not found. Skipping context7 global install."
fi

# 6. Initialize Environment File
if [ ! -f .env ]; then
    echo "Initializing .env file from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        echo "# Config template" > .env
    fi
fi

echo "============================================="
echo "Setup complete!"
echo "1. Activate venv: source venv/bin/activate"
echo "2. Edit .env file with API keys."
echo "3. Run CLI test: PYTHONPATH=. python3 src/run_cli.py"
echo "4. Run Telegram bot: PYTHONPATH=. python3 src/run_telegram.py"
echo "============================================="
