#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/patfaint/the-butler.git"
APP_ROOT="/opt/the-butler"
APP_DIR="${APP_ROOT}/app"
DATA_DIR="${APP_ROOT}/data"
LOG_DIR="${APP_ROOT}/logs"
SERVICE_NAME="the-butler"
RUNTIME_USER="butlerbot"
PYTHON_BIN=""

if [[ "${EUID}" -ne 0 || -z "${SUDO_USER:-}" || "${SUDO_USER}" == "root" ]]; then
  echo "This installer must be run with sudo by the non-root deploy user."
  echo "Usage: sudo bash install.sh"
  exit 1
fi

DEPLOY_OWNER="${SUDO_USER}"
DEPLOY_GROUP="$(id -gn "${DEPLOY_OWNER}")"

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This installer currently supports Debian/Ubuntu systems with apt-get."
  exit 1
fi

prompt_value() {
  local name="$1"
  local value=""
  while [[ -z "${value}" ]]; do
    read -r -p "${name}: " value
  done
  printf '%s' "${value}"
}

prompt_secret() {
  local name="$1"
  local value=""
  while [[ -z "${value}" ]]; do
    read -r -s -p "${name}: " value
    echo
  done
  printf '%s' "${value}"
}

echo "Installing system packages..."
apt-get update
apt-get install -y git python3 python3-venv python3-pip software-properties-common

if ! command -v python3.11 >/dev/null 2>&1; then
  if [[ -r /etc/os-release ]]; then
    # shellcheck source=/dev/null
    . /etc/os-release
    if [[ "${ID:-}" == "ubuntu" ]]; then
      add-apt-repository -y ppa:deadsnakes/ppa
      apt-get update
    fi
  fi
fi

apt-get install -y python3.11 python3.11-venv
PYTHON_BIN="$(command -v python3.11)"

if ! "${PYTHON_BIN}" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
then
  echo "Python 3.11 or newer is required. Install Python 3.11+ and run this installer again."
  exit 1
fi

echo "Creating runtime user..."
if ! getent group "${RUNTIME_USER}" >/dev/null 2>&1; then
  groupadd --system "${RUNTIME_USER}"
fi

if ! id "${RUNTIME_USER}" >/dev/null 2>&1; then
  useradd --system --gid "${RUNTIME_USER}" --home-dir "${APP_ROOT}" --shell /usr/sbin/nologin "${RUNTIME_USER}"
fi

echo "Creating directories..."
mkdir -p "${APP_DIR}" "${DATA_DIR}" "${LOG_DIR}"

echo "Cloning repository..."
if [[ -d "${APP_DIR}/.git" ]]; then
  git -C "${APP_DIR}" fetch origin main
  git -C "${APP_DIR}" reset --hard origin/main
else
  rm -rf "${APP_DIR}"
  git clone "${REPO_URL}" "${APP_DIR}"
fi

mkdir -p "${APP_DIR}/data"

echo "Creating Python virtual environment..."
"${PYTHON_BIN}" -m venv "${APP_DIR}/.venv"
"${APP_DIR}/.venv/bin/python" -m pip install --upgrade pip
"${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

echo "Enter Discord and server configuration."
DISCORD_TOKEN="$(prompt_secret "DISCORD_TOKEN")"
read -r -p "GUILD_ID (optional): " GUILD_ID
WELCOME_CHANNEL_ID="$(prompt_value "WELCOME_CHANNEL_ID")"
VERIFICATION_CHANNEL_ID="$(prompt_value "VERIFICATION_CHANNEL_ID")"
VERIFY_LOG_CHANNEL_ID="$(prompt_value "VERIFY_LOG_CHANNEL_ID")"
GENERAL_CHANNEL_ID="$(prompt_value "GENERAL_CHANNEL_ID")"
ROLES_CHANNEL_ID="$(prompt_value "ROLES_CHANNEL_ID")"
INTRODUCTIONS_CHANNEL_ID="$(prompt_value "INTRODUCTIONS_CHANNEL_ID")"
UNVERIFIED_ROLE_ID="$(prompt_value "UNVERIFIED_ROLE_ID")"
VERIFIED_ROLE_ID="$(prompt_value "VERIFIED_ROLE_ID")"
DOMME_ROLE_ID="$(prompt_value "DOMME_ROLE_ID")"
SUBMISSIVE_ROLE_ID="$(prompt_value "SUBMISSIVE_ROLE_ID")"
MODERATION_ROLE_ID="$(prompt_value "MODERATION_ROLE_ID")"

cat > "${APP_DIR}/.env" <<ENV
DISCORD_TOKEN=${DISCORD_TOKEN}
GUILD_ID=${GUILD_ID}
WELCOME_CHANNEL_ID=${WELCOME_CHANNEL_ID}
VERIFICATION_CHANNEL_ID=${VERIFICATION_CHANNEL_ID}
VERIFY_LOG_CHANNEL_ID=${VERIFY_LOG_CHANNEL_ID}
GENERAL_CHANNEL_ID=${GENERAL_CHANNEL_ID}
ROLES_CHANNEL_ID=${ROLES_CHANNEL_ID}
INTRODUCTIONS_CHANNEL_ID=${INTRODUCTIONS_CHANNEL_ID}
UNVERIFIED_ROLE_ID=${UNVERIFIED_ROLE_ID}
VERIFIED_ROLE_ID=${VERIFIED_ROLE_ID}
DOMME_ROLE_ID=${DOMME_ROLE_ID}
SUBMISSIVE_ROLE_ID=${SUBMISSIVE_ROLE_ID}
MODERATION_ROLE_ID=${MODERATION_ROLE_ID}
DATABASE_PATH=data/the_butler.sqlite3
ENV

chmod 600 "${APP_DIR}/.env"
chown "${RUNTIME_USER}:${RUNTIME_USER}" "${APP_DIR}/.env"
chown -R "${RUNTIME_USER}:${RUNTIME_USER}" "${DATA_DIR}" "${LOG_DIR}"
chown -R "${DEPLOY_OWNER}:${DEPLOY_GROUP}" "${APP_DIR}"
chown -R "${RUNTIME_USER}:${RUNTIME_USER}" "${APP_DIR}/data"
chown "${RUNTIME_USER}:${RUNTIME_USER}" "${APP_DIR}/.env"

echo "Installing systemd service..."
install -m 0644 "${APP_DIR}/the-butler.service" "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}"

echo
echo "The Butler is installed."
echo
echo "Status command:"
echo "  sudo systemctl status ${SERVICE_NAME}"
echo
echo "Logs command:"
echo "  sudo journalctl -u ${SERVICE_NAME} -f"
echo
echo "Restart command:"
echo "  sudo systemctl restart ${SERVICE_NAME}"
