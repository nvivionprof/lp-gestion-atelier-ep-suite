#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="backups/pre_upgrade_$STAMP"
ARCHIVE="backups/pre_upgrade_$STAMP.tar.gz"
mkdir -p "$BACKUP_DIR/sqlite_dumps"

log(){ echo "[$(date +%H:%M:%S)] $*"; }
copy_if_exists(){ [ -e "$1" ] && cp -a "$1" "$2" 2>/dev/null || true; }

log "Création sauvegarde pré-upgrade : $BACKUP_DIR"
copy_if_exists .env "$BACKUP_DIR/env.backup"
copy_if_exists manifest.json "$BACKUP_DIR/manifest_before_upgrade.json"
cp -a VERSION* "$BACKUP_DIR/" 2>/dev/null || true
[ -d imports ] && cp -a imports "$BACKUP_DIR/imports" 2>/dev/null || true

for data_dir in \
  lp-core-db/data \
  toolmag-db/data \
  safety-db/data \
  pedashop-db/data \
  system-manager-db/data \
  tpmanager-db/data
 do
  if [ -d "$data_dir" ]; then
    safe_name="$(echo "$data_dir" | tr '/-' '__')"
    cp -a "$data_dir" "$BACKUP_DIR/$safe_name" 2>/dev/null || true
  fi
 done

sqlite_dump(){
  local service="$1"
  local src="$2"
  local out_name="$3"
  local cid="$(docker compose ps -q "$service" 2>/dev/null || true)"
  if [ -n "$cid" ]; then
    local running="$(docker inspect -f '{{.State.Running}}' "$cid" 2>/dev/null || echo false)"
    if [ "$running" != "true" ]; then
      log "AVERTISSEMENT : dump SQLite ignoré pour $service, conteneur non démarré ou en redémarrage"
      return 0
    fi
    log "Dump SQLite : $service"
    docker compose exec -T "$service" sh -lc "python - <<'PY'
import os, sqlite3
src='$src'
out='/tmp/$out_name.sql'
if os.path.exists(src):
    con=sqlite3.connect(src)
    with open(out, 'w', encoding='utf-8') as f:
        for line in con.iterdump():
            f.write(line + '\\n')
    con.close()
PY" || true
    docker compose cp "$service:/tmp/$out_name.sql" "$BACKUP_DIR/sqlite_dumps/$out_name.sql" >/dev/null 2>&1 || true
  fi
}

sqlite_dump lp-core-app "/data/lp-core/lp-core.sqlite3" "lp-core-db"
sqlite_dump toolmag-app "/data/toolmag/toolmag.sqlite3" "toolmag-db"
sqlite_dump safety-app "/data/safety/safety.sqlite3" "safety-db"
sqlite_dump pedashop-app "/data/pedashop/pedashop.sqlite3" "pedashop-db"
sqlite_dump system-manager-app "/data/system-manager/system-manager.sqlite3" "system-manager-db"
sqlite_dump tpmanager-app "/data/tpmanager/tpmanager.sqlite3" "tpmanager-db"

tar -czf "$ARCHIVE" -C backups "$(basename "$BACKUP_DIR")"
echo "$BACKUP_DIR" > backups/LAST_PRE_UPGRADE_BACKUP.txt
log "Sauvegarde pré-upgrade créée : $BACKUP_DIR"
log "Archive : $ARCHIVE"
