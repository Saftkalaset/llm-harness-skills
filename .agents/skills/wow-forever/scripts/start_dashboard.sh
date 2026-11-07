#!/usr/bin/env bash
# Quick launcher for Saftis WoW Forever Progression Dashboard & Sync Daemon
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/render_progression_dashboard.py"
PORT=18765

# 1. Check if the disk auto-save sync daemon is already running
if curl -s -f "http://127.0.0.1:${PORT}/state" >/dev/null 2>&1; then
    echo "✓ Sync daemon is already running on http://127.0.0.1:${PORT}/state"
else
    echo "Starting disk auto-save sync daemon on port ${PORT}..."
    nohup python3 "${PYTHON_SCRIPT}" --serve-sync >/tmp/wow_forever_sync.log 2>&1 &
    sleep 1
    if curl -s -f "http://127.0.0.1:${PORT}/state" >/dev/null 2>&1; then
        echo "✓ Sync daemon started successfully (PID: $!). Log: /tmp/wow_forever_sync.log"
    else
        echo "⚠️ Warning: Sync daemon failed to respond immediately. Check /tmp/wow_forever_sync.log"
    fi
fi

# 2. Recompile latest dashboard and open in Firefox
echo "Compiling dashboard and opening in Firefox..."
python3 "${PYTHON_SCRIPT}" --open
echo "Done! Dashboard is live."
