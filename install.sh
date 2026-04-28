#!/usr/bin/env bash
# install.sh — One-time EC2 setup script for The Butler Discord bot
# Run as root or with sudo: sudo bash install.sh

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✔]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✘]${NC} $*" >&2; exit 1; }

# ── Root check ───────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
  error "This script must be run as root. Try: sudo bash install.sh"
fi

REPO_URL="https://github.com/patfaint/the-butler.git"
BOT_USER="butler"
BOT_HOME="/home/butler"
BOT_DIR="${BOT_HOME}/the-butler"
SERVICE_NAME="the-butler"
SERVICE_FILE="/etc/systemd/system/"){SERVICE_NAME}.service"

echo ""
echo "🎩 The Butler — EC2 Installation Script"
echo "========================================"
echo ""

# ── 1. Detect OS and install packages ────────────────────────────────────────
info "Detecting operating system..."

if command -v apt-get &>/dev/null; then
  OS="ubuntu"
  info "Detected Ubuntu/Debian. Adding deadsnakes PPA for Python 3.12..."
  apt-get update -y -qq
  apt-get install -y -qq software-properties-common
  add-apt-repository ppa:deadsnakes/ppa -y
  apt-get update -y -qq
  apt-get install -y -qq python3.12 python3.12-venv python3.12-distutils python3-pip git screen curl
elif command -v yum &>/dev/null; then
  OS="amazon"
  info "Detected Amazon Linux / RHEL. Updating packages..."
  yum update -y -q
  if yum list available python3.12 &>/dev/null 2>&1; then
    yum install -y -q python3.12 git screen
  else
    warn "python3.12 not in default repos — installing from source or extras..."
    yum install -y -q gcc openssl-devel bzip2-devel libffi-devel zlib-devel git screen curl
    cd /tmp
    curl -fsSL https://www.python.org/ftp/python/3.12.4/Python-3.12.4.tgz -o Python-3.12.4.tgz
    tar -xzf Python-3.12.4.tgz
    cd Python-3.12.4
    ./configure --enable-optimizations --quiet
    make altinstall -j"$(nproc)" > /dev/null
    cd /
    rm -rf /tmp/Python-3.12.4 /tmp/Python-3.12.4.tgz
  fi
  python3.12 -m ensurepip --upgrade 2>/dev/null || true
else
  error "Unsupported OS. This script supports Ubuntu/Debian and Amazon Linux."
fi

info "System packages installed."

# ── 2. Create the butler system user ─────────────────────────────────────────
if id "${BOT_USER}" &>/dev/null; then
  warn "User '${BOT_USER}' already exists — skipping creation."
else
  info "Creating system user '${BOT_USER}'..."
  useradd --system --create-home --home-dir "${BOT_HOME}" --shell /bin/bash "${BOT_USER}"
  info "User '${BOT_USER}' created."
fi

# ── 3. Clone or update the repository ────────────────────────────────────────
if [[ -d "${BOT_DIR}/.git" ]]; then
  warn "Repository already exists at ${BOT_DIR} — pulling latest changes..."
  sudo -u "${BOT_USER}" git -C "${BOT_DIR}" pull --ff-only
  info "Repository updated."
else
  info "Cloning repository to ${BOT_DIR}..."
  sudo -u "${BOT_USER}" git clone "${REPO_URL}" "${BOT_DIR}"
  info "Repository cloned."
fi

# ── 4. Python 3.12 virtual environment ───────────────────────────────────────
PYTHON_BIN="$(command -v python3.12)"
info "Using Python: ${PYTHON_BIN} ($(${PYTHON_BIN} --version))"

VENV_DIR="${BOT_DIR}/venv"

if [[ -d "${VENV_DIR}" ]]; then
  warn "Virtual environment already exists — skipping creation."
else
  info "Creating Python 3.12 virtual environment..."
  sudo -u "${BOT_USER}" "${PYTHON_BIN}" -m venv "${VENV_DIR}"
  info "Virtual environment created."
fi

info "Installing Python dependencies from requirements.txt..."
sudo -u "${BOT_USER}" "${VENV_DIR}/bin/pip" install --quiet --upgrade pip
sudo -u "${BOT_USER}" "${VENV_DIR}/bin/pip" install --quiet -r "${BOT_DIR}/requirements.txt"
info "Dependencies installed."

# ── 5. Environment variables (.env) ──────────────────────────────────────────
ENV_FILE="${BOT_DIR}/.env"

if [[ -f "${ENV_FILE}" ]]; then
  warn ".env file already exists at ${ENV_FILE} — skipping prompt."
else
  echo ""
  echo "🔑 Environment Configuration"
  echo "----------------------------"
  echo "Please provide the following values. Press Enter to accept the default where shown."
  echo ""
  
  read -rp "  DISCORD_TOKEN: " DISCORD_TOKEN
  while [[ -z "${DISCORD_TOKEN}" ]]; do
    warn "DISCORD_TOKEN cannot be empty."
    read -rp "  DISCORD_TOKEN: " DISCORD_TOKEN
  done
  
  read -rp "  GIPHY_API_KEY (leave blank to skip): " GIPHY_API_KEY
  
  read -rp "  GUILD_ID: " GUILD_ID
  while [[ -z "${GUILD_ID}" ]]; do
    warn "GUILD_ID cannot be empty."
    read -rp "  GUILD_ID: " GUILD_ID
  done
  
  read -rp "  DATABASE_URL [sqlite+aiosqlite:///./butler.db]: " DATABASE_URL
  DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./butler.db}"
  
  info "Writing .env file..."
  cat > "${ENV_FILE}" <<EOF
DISCORD_TOKEN=${DISCORD_TOKEN}
GIPHY_API_KEY=${GIPHY_API_KEY}
GUILD_ID=${GUILD_ID}
DATABASE_URL=${DATABASE_URL}
EOF
  
  chown "${BOT_USER}:${BOT_USER}" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
  info ".env file created."
fi

# ── 6. Systemd service ────────────────────────────────────────────────────────
info "Creating systemd service file at ${SERVICE_FILE}..."

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=The Butler Discord Bot
After=network.target

[Service]
Type=simple
User=${BOT_USER}
WorkingDirectory=${BOT_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${VENV_DIR}/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"
info "Service '${SERVICE_NAME}' enabled and started."

# ── 7. Fix ownership ─────────────────────────────────────────────────────────
chown -R "${BOT_USER}:${BOT_USER}" "${BOT_HOME}"

# ── 8. Final summary ─────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}🎩 The Butler has been installed and is now at your service.${NC}"
echo ""
echo "Useful commands:"
echo "  Check status:   sudo systemctl status ${SERVICE_NAME}"
echo "  View logs:      sudo journalctl -u ${SERVICE_NAME} -f"
echo "  Restart bot:    sudo systemctl restart ${SERVICE_NAME}"
echo "  Update bot:     sudo bash ${BOT_DIR}/update.sh"
echo ""