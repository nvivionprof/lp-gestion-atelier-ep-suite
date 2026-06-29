#!/usr/bin/env bash
set -euo pipefail
source /etc/lp-display-player.env
URL="${LPDISPLAY_BASE_URL}/player/${LPDISPLAY_PLAYER_TOKEN}/"

xset s off || true
xset -dpms || true
xset s noblank || true
unclutter -idle 0.5 -root &

while true; do
  chromium-browser \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --kiosk \
    --autoplay-policy=no-user-gesture-required \
    "${URL}"
  sleep 5
 done
