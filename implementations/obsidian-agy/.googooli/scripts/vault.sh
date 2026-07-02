#!/bin/bash
# Googooli Vault Lock/Unlock
# Usage: ./vault.sh lock | unlock

VAULT_DIR="$HOME/.notebooklm/profiles/default"
SECRET_FILE="$VAULT_DIR/storage_state.json"
ENC_FILE="$VAULT_DIR/storage_state.json.enc"

if [ "$1" == "lock" ]; then
    if [ -f "$SECRET_FILE" ]; then
        echo "🔒 Googooli: Locking credentials..."
        openssl enc -aes-256-cbc -salt -pbkdf2 -in "$SECRET_FILE" -out "$ENC_FILE"
        if [ $? -eq 0 ]; then
            rm "$SECRET_FILE"
            echo "✅ Locked. Plaintext file removed."
        else
            echo "❌ Encryption failed."
        fi
    else
        echo "⚠️ No plaintext file found to lock."
    fi
elif [ "$1" == "unlock" ]; then
    if [ -f "$ENC_FILE" ]; then
        echo "🔓 Googooli: Unlocking credentials..."
        openssl enc -d -aes-256-cbc -pbkdf2 -in "$ENC_FILE" -out "$SECRET_FILE"
        if [ $? -eq 0 ]; then
            echo "✅ Unlocked. NotebookLM is ready."
        else
            echo "❌ Decryption failed. Wrong password?"
        fi
    else
        echo "⚠️ No encrypted file found."
    fi
else
    echo "Usage: $0 lock | unlock"
fi
