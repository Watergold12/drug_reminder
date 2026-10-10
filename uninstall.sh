#!/bin/bash
# ============================================================================
# 💊 Drug Remainder — Uninstaller
# ============================================================================
# Removes the Drug Remainder systemd service. Does NOT delete your data/logs.
# ============================================================================

set -euo pipefail

SERVICE_NAME="drug_remainder.service"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "💊 Drug Remainder — Uninstallation"
echo "===================================="
echo ""

# Stop and disable
echo "🛑 Stopping service..."
systemctl --user stop "$SERVICE_NAME" 2>/dev/null || true
systemctl --user disable "$SERVICE_NAME" 2>/dev/null || true

# Remove service file
echo "🗑️  Removing service file..."
rm -f "$SYSTEMD_USER_DIR/$SERVICE_NAME"
systemctl --user daemon-reload

# Remove global shortcut
echo "🗑️  Removing global shortcut..."
rm -f "$HOME/.local/bin/drug_remainder"

echo ""
echo "✅ Drug Remainder service has been removed."
echo ""
echo "   Your data and logs are still in:"
echo "   $SCRIPT_DIR/data/"
echo ""
echo "   To delete everything:"
echo "   rm -rf $SCRIPT_DIR"
echo ""
echo "   \"Your prescription has been cancelled."
echo "    But your dehydration? That's still active.\""
echo ""
