#!/bin/bash
# ============================================================================
# 💊 Drug Remainder — Installer
# ============================================================================
# Installs the Drug Remainder hydration service as a systemd user service.
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="drug_remainder.service"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo ""
echo "💊 Drug Remainder — Installation"
echo "================================="
echo ""

# 1. Check dependencies
echo "🔍 Checking dependencies..."

check_dep() {
    if ! command -v "$1" &>/dev/null; then
        echo "  ❌ $1 not found. Install with: $2"
        return 1
    else
        echo "  ✅ $1 found"
        return 0
    fi
}

DEPS_OK=true
check_dep python3 "sudo apt install python3" || DEPS_OK=false
check_dep notify-send "sudo apt install libnotify-bin" || DEPS_OK=false
check_dep paplay "sudo apt install pulseaudio-utils" || DEPS_OK=false

if [ "$DEPS_OK" = false ]; then
    echo ""
    echo "⚠️  Some dependencies are missing. Install them and try again."
    exit 1
fi

# 2. Check Python venv and packages
echo ""
echo "🐍 Checking Python environment..."
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
fi

echo "  Installing Python dependencies..."
"$SCRIPT_DIR/venv/bin/pip" install -q schedule

echo "  ✅ Python environment ready"

# 3. Create data directories
echo ""
echo "📁 Creating data directories..."
mkdir -p "$SCRIPT_DIR/data/logs"
echo "  ✅ Data directories created"

# 4. Install systemd user service
echo ""
echo "⚙️  Installing systemd user service..."
mkdir -p "$SYSTEMD_USER_DIR"

# Generate service file with absolute paths
cat > "$SYSTEMD_USER_DIR/$SERVICE_NAME" << EOF
[Unit]
Description=Drug Remainder — Hydration Prescription Service
After=graphical-session.target

[Service]
Type=simple
ExecStart=$SCRIPT_DIR/venv/bin/python3 $SCRIPT_DIR/drug_remainder.py
WorkingDirectory=$SCRIPT_DIR
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus

[Install]
WantedBy=default.target
EOF

echo "  ✅ Service file installed"

# 5. Enable and start the service
echo ""
echo "🚀 Enabling and starting service..."
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user start "$SERVICE_NAME"
echo "  ✅ Service enabled and started"

# 6. Verify
echo ""
echo "🔍 Verifying..."
if systemctl --user is-active --quiet "$SERVICE_NAME"; then
    echo "  ✅ Drug Remainder is running!"
else
    echo "  ⚠️  Service may not have started. Check with:"
    echo "     systemctl --user status drug_remainder"
fi

# 7. Sarcastic welcome
echo ""
echo "============================================="
echo "💊 Your prescription has been filled."
echo ""
echo "   Drug Remainder is now monitoring your"
echo "   hydration levels. Remember:"
echo ""
echo "   Water isn't optional."
echo "   Neither is this service."
echo ""
echo "   Useful commands:"
echo "     ./drug_remainder.py --stats"
echo "     ./drug_remainder.py --roast-me"
echo "     ./drug_remainder.py --achievements"
echo "     ./drug_remainder.py --test-notification"
echo "============================================="
echo ""
