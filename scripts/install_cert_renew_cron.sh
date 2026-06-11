#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"
CRON_LINE="17 3 * * * cd $PROJECT_DIR && ./scripts/cert_manager.sh renew >> $PROJECT_DIR/ssl/renew.log 2>&1"
( crontab -l 2>/dev/null | grep -v 'cert_manager.sh renew' ; echo "$CRON_LINE" ) | crontab -
echo "Renouvellement quotidien installé dans la crontab utilisateur."
echo "$CRON_LINE"
