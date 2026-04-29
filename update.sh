#!/usr/bin/env bash
# update.sh — Pull the latest code and restart The Butler service.
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

# ── Root check ────────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
  error "This script must be run as root. Try: sudo bash update.sh"
fi

BOT_USER="butler"
BOT_HOME="/home/butler"
BOT_DIR="${BOT_HOME}/the-butler"
VENV_DIR="${BOT_DIR}/venv"
SERVICE_NAME="the-butler"

echo ""
echo "🎩 The Butler — Update Script"
echo "=============================="
echo ""

# ── 1. Pull latest code ───────────────────────────────────────────────────────
info "Pulling latest changes from GitHub..."
sudo -u "${BOT_USER}" git -C "${BOT_DIR}" fetch --prune
sudo -u "${BOT_USER}" git -C "${BOT_DIR}" reset --hard origin/main
info "Code updated."

# ── 2. Install / upgrade Python dependencies ─────────────────────────────────
info "Upgrading Python dependencies..."
sudo -u "${BOT_USER}" "${VENV_DIR}/bin/pip" install --quiet --upgrade pip
sudo -u "${BOT_USER}" "${VENV_DIR}/bin/pip" install --quiet --upgrade -r "${BOT_DIR}/requirements.txt"
info "Dependencies up-to-date."

# ── 3. Fix ownership (in case new files were pulled) ─────────────────────────
chown -R "${BOT_USER}:${BOT_USER}" "${BOT_HOME}"

# ── 4. Restart the service ────────────────────────────────────────────────────
info "Restarting ${SERVICE_NAME} service..."
systemctl restart "${SERVICE_NAME}"
info "Service restarted."

# ── 5. Status check ───────────────────────────────────────────────────────────
sleep 2
if systemctl is-active --quiet "${SERVICE_NAME}"; then
  info "The Butler is active and at your service. 🎩"
else
  error "Service failed to start. Run: sudo journalctl -u ${SERVICE_NAME} -n 50 --no-pager"
fi

echo ""
