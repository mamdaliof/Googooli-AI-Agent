#!/bin/bash
# setup_systemd_timers.sh - Sets up Phase 1 and Phase 2 systemd timers dynamically.

REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO_DIR" ]; then
    REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi

SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

echo "⚙️ Creating Phase 1 Service & Timer..."
cat <<EOF > "$SYSTEMD_DIR/googooli-phase1.service"
[Unit]
Description=Googooli Phase 1 Ingestion
After=network.target

[Service]
Type=oneshot
Environment="TZ=Europe/Amsterdam"
WorkingDirectory=$REPO_DIR
ExecStart=/usr/bin/bash -c "source $REPO_DIR/.googooli/venv/bin/activate && python3 $REPO_DIR/.googooli/scripts/research_assistant.py --phase1"
EOF

cat <<EOF > "$SYSTEMD_DIR/googooli-phase1.timer"
[Unit]
Description=Run Googooli Phase 1 daily at 1:00 AM Europe/Amsterdam

[Timer]
OnCalendar=*-*-* 01:00:00
TimeZone=Europe/Amsterdam
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "⚙️ Creating Phase 2 Service & Timer..."
cat <<EOF > "$SYSTEMD_DIR/googooli-phase2.service"
[Unit]
Description=Googooli Phase 2 Ingestion
After=network.target

[Service]
Type=oneshot
Environment="TZ=Europe/Amsterdam"
WorkingDirectory=$REPO_DIR
ExecStart=/usr/bin/bash -c "source $REPO_DIR/.googooli/venv/bin/activate && python3 $REPO_DIR/.googooli/scripts/research_assistant.py --phase2"
EOF

cat <<EOF > "$SYSTEMD_DIR/googooli-phase2.timer"
[Unit]
Description=Run Googooli Phase 2 daily at 6:00 AM Europe/Amsterdam

[Timer]
OnCalendar=*-*-* 06:00:00
TimeZone=Europe/Amsterdam
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "⚙️ Creating Googooli Telegram Gateway Service..."
cat <<EOF > "$SYSTEMD_DIR/googooli-gateway.service"
[Unit]
Description=Googooli Telegram Gateway
After=network.target

[Service]
Type=simple
WorkingDirectory=$REPO_DIR
ExecStart=/usr/bin/bash $REPO_DIR/.googooli/scripts/run_gateway.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

echo "🔄 Reloading systemd daemon..."
systemctl --user daemon-reload

echo "🚀 Enabling and starting services and timers..."
systemctl --user enable --now googooli-gateway.service
systemctl --user enable --now googooli-phase1.timer
systemctl --user enable --now googooli-phase2.timer

echo "📊 Checking status..."
systemctl --user list-timers --all | grep googooli
systemctl --user status googooli-gateway.service --no-pager

echo "✅ Systemd services and timers configured successfully."
