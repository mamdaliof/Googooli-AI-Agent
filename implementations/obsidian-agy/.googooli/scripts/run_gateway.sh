#!/bin/bash
# Googooli Telegram Gateway Runner

# Load paths
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
export GOOGOOLI_DEV=true

set -a
source .googooli/config/.env
set +a
/usr/bin/python3 -u .googooli/scripts/telegram_gateway.py
