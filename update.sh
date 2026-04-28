#!/usr/bin/env bash
# update.sh — Pull the latest code and restart The Butler
# Run as root or with sudo: sudo bash /home/butler/the-butler/update.sh

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✔]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✘]${NC} $*" >&2; exit 1; }

# These values must match those used in install.sh.
BOT_USER="butler"
BOT_DIR="/home/butler/the-butler"
VENV_DIR="${BOT_DIR}/venv"
SERVICE_NAME="the-butler"

# ── Root check ────────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
  error "This script must be run as root. Try: sudo bash ${BOT_DIR}/update.sh"
fi

echo ""
echo "🎩 The Butler — Update Script"
echo "=============================="
echo ""

# ── 1. Pull latest code ───────────────────────────────────────────────────────
info "Pulling latest code from GitHub..."
sudo -u "${BOT_USER}" git -C "${BOT_DIR}" pull --ff-only
info "Code updated."

# ── 2. Reinstall dependencies ─────────────────────────────────────────────────
info "Reinstalling Python dependencies..."
sudo -u "${BOT_USER}" "${VENV_DIR}/bin/pip" install --quiet --upgrade pip
sudo -u "${BOT_USER}" "${VENV_DIR}/bin/pip" install --quiet -r "${BOT_DIR}/requirements.txt"
info "Dependencies up to date."

# ── 3. Restart the service ────────────────────────────────────────────────────
info "Restarting ${SERVICE_NAME} service..."
systemctl daemon-reload
systemctl restart "${SERVICE_NAME}"
info "Service restarted."

echo ""
echo -e "${GREEN}🎩 The Butler has been updated and is back at your service.${NC}"
echo ""
echo "  Check status:   sudo systemctl status ${SERVICE_NAME}"
echo "  View logs:      sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
