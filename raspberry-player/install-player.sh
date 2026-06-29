#!/usr/bin/env bash
set -euo pipefail

if [ "${EUID}" -ne 0 ]; then
  echo "Lancer ce script avec sudo." >&2
  exit 1
fi

BASE_URL="${1:-}"
TOKEN="${2:-}"

if [ -z "${BASE_URL}" ] || [ -z "${TOKEN}" ]; then
  echo "Usage: sudo ./install-player.sh http://serveur:9000/lpdisplaymanager TOKEN_PLAYER" >&2
  exit 1
fi

apt-get update
apt-get install -y chromium-browser unclutter python3 python3-requests x11-xserver-utils

mkdir -p /opt/lp-display-player
cp lp-display-agent.py /opt/lp-display-player/lp-display-agent.py
cp kiosk-start.sh /opt/lp-display-player/kiosk-start.sh
chmod +x /opt/lp-display-player/*.py /opt/lp-display-player/*.sh

cat >/etc/lp-display-player.env <<EOF
LPDISPLAY_BASE_URL=${BASE_URL}
LPDISPLAY_PLAYER_TOKEN=${TOKEN}
EOF

cp lp-display-agent.service /etc/systemd/system/lp-display-agent.service
cp lp-kiosk.service /etc/systemd/system/lp-kiosk.service

systemctl daemon-reload
systemctl enable lp-display-agent.service
systemctl enable lp-kiosk.service
systemctl restart lp-display-agent.service
systemctl restart lp-kiosk.service

echo "Player installé. URL kiosk: ${BASE_URL}/player/${TOKEN}/"
