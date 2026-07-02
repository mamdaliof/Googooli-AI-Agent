#!/bin/bash
# setup_agent.sh - Auto-initialization script for Googooli Assistant.

echo "============================================================"
echo "🚀 Initializing Googooli Assistant environment & packages..."
echo "============================================================"

# Resolve directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 1. Create Python virtual environment if not present
echo "📦 Setting up Python virtual environment..."
if [ ! -d "$BASE_DIR/venv" ]; then
    python3 -m venv "$BASE_DIR/venv"
    if [ $? -ne 0 ]; then
        echo "❌ FAILED to create virtual environment. Attempting global/user install instead."
    fi
fi

# 2. Activate virtual environment if it exists
if [ -d "$BASE_DIR/venv" ]; then
    source "$BASE_DIR/venv/bin/activate"
    echo "✅ Virtual environment activated."
fi

# 3. Upgrade pip and install dependencies
echo "📥 Installing required Python packages..."
pip install --upgrade pip
pip install pyTelegramBotAPI markdown2 requests beautifulsoup4 python-docx jieba tavily-python

if [ $? -ne 0 ]; then
    echo "⚠️ Pip failed. Retrying with --break-system-packages (PEP 668 bypass)..."
    pip install --break-system-packages pyTelegramBotAPI markdown2 requests beautifulsoup4 python-docx jieba tavily-python
fi

if [ $? -eq 0 ]; then
    echo "✅ Python libraries successfully installed."
else
    echo "❌ FAILED installing some libraries. Please review pip logs."
fi

# 4. Initialize Database
echo "🗄️ Initializing SQLite state tracking database..."
python3 "$SCRIPT_DIR/init_db.py"

# 5. Run diagnostics check
echo "🩺 Running Googooli diagnostics checklist..."
bash "$SCRIPT_DIR/check_dependencies.sh"

echo "============================================================"
echo "🎉 Setup complete! Googooli environment is ready."
echo "============================================================"
