#!/bin/bash
# Googooli Pre-Request Sync
# Triggered by BeforeAgent hook

# Find git root reliably
REPO_DIR=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_DIR" ]; then
    echo "❌ Googooli: Not in a git repository." >&2
    echo "{}"
    exit 0
fi
cd "$REPO_DIR"

echo "🔄 Googooli: Pulling latest changes..." >&2
git pull origin main --no-edit >&2 || echo "⚠️ Pull failed. Check for conflicts." >&2

# Required: Output JSON to stdout for Gemini hooks
echo "{}"
