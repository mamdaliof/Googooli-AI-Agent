#!/bin/bash
# Googooli Auto-Sync Engine
# Every 1 minute: pull -> merge -> commit -> push

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../" && pwd)"
cd "$REPO_DIR"

while true; do
    echo "--- Googooli Sync Start: $(date) ---"
    
    # 1. Pull changes
    git pull origin main --no-edit
    
    # 2. Check for changes to commit
    if [[ -n $(git status -s) ]]; then
        git add .
        git commit -m "chore(sync): automated vault sync [$(hostname)]"
        git push origin main
        echo "Changes synced."
    else
        echo "No changes to sync."
    fi
    
    sleep 60
done
