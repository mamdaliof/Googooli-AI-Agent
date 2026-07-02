#!/bin/bash
# Googooli Server Setup Script
# Detects environment and configures local .gemini/settings.json

HOSTNAME=$(hostname)
VAULT_PATH=$(pwd)
CONFIG_FILE="$VAULT_PATH/.googooli/config/googooli-config.json"

echo "🔧 Googooli: Setting up for environment: $HOSTNAME"

if [[ "$HOSTNAME" == *"server"* ]] || [[ "$HOSTNAME" == "ubuntu-s-"* ]]; then
    DEVICE_TYPE="server"
    APPROVAL="yolo"
    TELEGRAM="true"
else
    DEVICE_TYPE="personal_pc"
    APPROVAL="auto_edit"
    TELEGRAM="false"
fi

# Update the hidden config
sed -i "s/SERVER_OR_PC_ID/$HOSTNAME/" "$CONFIG_FILE"

echo "🤖 Googooli: Checking NotebookLM environment..."
if ! command -v notebooklm &> /dev/null && ! command -v ~/.local/bin/notebooklm &> /dev/null; then
    echo "📦 Installing notebooklm-py and dependencies..."
    pip install --user --break-system-packages "notebooklm-py[browser]" pyTelegramBotAPI markdown2 jieba python-docx
    ~/.local/bin/playwright install chromium
fi

if [ ! -f ~/.notebooklm/profiles/default/storage_state.json ]; then
    echo "🔑 NotebookLM not authenticated. Starting login..."
    ~/.local/bin/notebooklm login
else
    echo "✅ NotebookLM is authenticated."
fi

echo "✅ Googooli configured as $DEVICE_TYPE with $APPROVAL mode."
