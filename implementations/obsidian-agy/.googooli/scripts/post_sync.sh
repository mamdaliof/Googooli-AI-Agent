#!/bin/bash
# Googooli Post-Request Sync
# Triggered by AfterAgent hook

# Find git root reliably
REPO_DIR=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_DIR" ]; then
    echo "❌ Googooli: Not in a git repository." >&2
    echo "{}"
    exit 0
fi
cd "$REPO_DIR"

if [[ -n $(git status -s) ]]; then
    echo "📤 Googooli: Generating smart commit..." >&2
    COMMIT_MSG="chore(sync): vault update [$(hostname)]"
    git add . >&2
    git commit -m "$COMMIT_MSG" >&2
    git push origin main >&2
else
    echo "✅ Googooli: No local changes to push." >&2
fi

# Required: Output JSON to stdout for Gemini hooks
echo "{}"
