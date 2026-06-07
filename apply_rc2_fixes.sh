#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"

log(){ echo "[RC2] $*"; }
write_file(){
  local path="$1"
  mkdir -p "$(dirname "$path")"
  cat > "$path"
}

log "Application des correctifs V0.0.1-RC2"

write_file scripts/set_env_value.sh <<'RC2EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 CLE VALEUR" >&2
  exit 1
fi

ENV_FILE=".env"
[ -f "$ENV_FILE" ] || cp .env.example "$ENV_FILE"

KEY="$1" VALUE="$2" ENV_FILE="$ENV_FILE" python3 - <<'PY'
import os
from pathlib import Path

path = Path(os.environ['ENV_FILE'])
key = os.environ['KEY']
value = os.environ['VALUE']
lines = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
out = []
found = False

for line in lines:
    stripped = line.strip()
    if stripped and not stripped.startswith('#') and '=' in stripped:
        current_key = stripped.split('=', 1)[0].strip()
        if current_key == key:
            out.append(f'{key}={value}')
            found = True
            continue
    out.append(line)

if not found:
    out.append(f'{key}={value}')
path.write_text('\n'.join(out) + '\n', encoding='utf-8')
PY
RC2EOF
chmod +x scripts/set_env_value.sh

write_file scripts/configure_install_env.sh <<'RC2EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE=".env"
[ -f "$ENV_FILE" ] || cp .env.example "$ENV_FILE"

set_env(){
  local key="$1"; shift
  local value="$*"
  ENV_FILE="$ENV_FILE" KEY="$key" VALUE="$value" python3 - <<'PY'
import os
from pathlib import Path

path = Path(os.environ['ENV_FILE'])
key = os.environ['KEY']
value = os.environ['VALUE']
lines = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
out = []
found = False
for line in lines:
    stripped = line.strip()
    if stripped and not stripped.startswith('#') and '=' in stripped:
        current_key = stripped.split('=', 1)[0].strip()
        if current_key == key:
            out.append(f'{key}={value}')
            found = True
            continue
    out.append(line)
if not found:
    out.append(f'{key}={value}')
path.write_text('\n'.join(out) + '\n', encoding='utf-8')
PY
}

get_env(){
  local key="$1"
  awk -F= -v k="$key" '$1==k{print substr($0,index($0,"=")+1)}' "$ENV_FILE" | tail -n 1
}

ask_secret_confirm(){
  local label="$1" var1 var2
  while true; do
    read -rsp "$label : " var1; echo >&2
    read -rsp "Confirme $label : " var2; echo >&2
    if [ -z "$var1" ]; then
      echo "Valeur vide interdite." >&2
    elif [ "$var1" != "$var2" ]; then
      echo "Les deux saisies ne correspondent pas." >&2
    else
      printf '%s' "$var1"
      return 0
    fi
  done
}

ask_text(){
  local label="$1" default="$2" value
  read -rp "$label [$default] : " value >&2
  value="${value:-$default}"
  printf '%s' "$value"
}

ask_yes_no(){
  local label="$1" default="${2:-N}" value
  read -rp "$label [$default] : " value >&2
  value="${value:-$default}"
  if [[ "$value" =~ ^[OoYy1]$ ]]; then printf '1'; else printf '0'; fi
}

validate_env(){
  python3 - <<'PY'
from pathlib import Path
import re
bad = []
path = Path('.env')
for i, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
    stripped = line.strip()
    if not stripped or stripped.startswith('#'):
        continue
    if '=' not in stripped:
        bad.append((i, line, "ligne sans '='"))
        continue
    key = stripped.split('=', 1)[0]
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', key):
        bad.append((i, line, 'clé invalide'))
if bad:
    for i, line, why in bad:
        print(f'.env invalide ligne {i}: {why}: {line!r}')
    raise SystemExit(1)
PY
}

CONFIG_MODE="${LP_INSTALL_MODE:-install}"
FORCE_DEMO_ARG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --mode) CONFIG_MODE="$2"; shift 2;;
    --mode=*) CONFIG_MODE="${1#*=}"; shift;;
    --demo) FORCE_DEMO_ARG=1; shift;;
    --no-demo) FORCE_DEMO_ARG=0; shift;;
    *) echo "Option inconnue pour configure_install_env.sh : $1" >&2; exit 1;;
  esac
done
case "$CONFIG_MODE" in install|update|upgrade) ;; *) echo "Mode invalide pour configure_install_env.sh : $CONFIG_MODE" >&2; exit 1;; esac

DB_PASS_ARG="${LP_INSTALL_DB_PASSWORD:-}"
ADMIN_USER_ARG="${LP_INSTALL_ADMIN_USERNAME:-}"
ADMIN_PASS_ARG="${LP_INSTALL_ADMIN_PASSWORD:-}"
LOAD_DEMO_ARG="${LP_INSTALL_LOAD_DEMO:-}"
[ -n "$FORCE_DEMO_ARG" ] && LOAD_DEMO_ARG="$FORCE_DEMO_ARG"

if [ -z "$DB_PASS_ARG" ]; then
  DB_PASS_ARG="$(ask_secret_confirm 'Mot de passe PostgreSQL lp_suite_user')"
fi
if [ -z "$ADMIN_USER_ARG" ]; then
  ADMIN_USER_ARG="$(ask_text 'Identifiant administrateur LP Core' "$(get_env LP_CORE_ADMIN_USERNAME || true)")"
  ADMIN_USER_ARG="${ADMIN_USER_ARG:-admin}"
fi
if [ -z "$ADMIN_PASS_ARG" ]; then
  ADMIN_PASS_ARG="$(ask_secret_confirm "Mot de passe administrateur LP Core (${ADMIN_USER_ARG})")"
fi

if [ "$CONFIG_MODE" = "install" ]; then
  if [ -z "$LOAD_DEMO_ARG" ]; then
    echo >&2
    echo "Bases de démonstration : choix d'installation initiale" >&2
    echo "- Oui : les données démo seront chargées automatiquement après les migrations." >&2
    echo "- Non : l'installation restera vide/propre, sans données de démonstration." >&2
    LOAD_DEMO_ARG="$(ask_yes_no 'Installer et charger les bases de démonstration ?' 'O')"
  fi
else
  LOAD_DEMO_ARG="0"
fi

set_env DB_ENGINE "django.db.backends.postgresql"
set_env POSTGRES_DB "lp_core"
set_env POSTGRES_USER "lp_suite_user"
set_env POSTGRES_PASSWORD "$DB_PASS_ARG"
set_env POSTGRES_HOST "postgres"
set_env POSTGRES_PORT "5432"
set_env POSTGRES_MULTIPLE_DATABASES "lp_core,toolmag,safety,pedashop,system_manager,tpmanager,pfmp"
set_env LP_CORE_DB_NAME "lp_core"
set_env TOOLMAG_DB_NAME "toolmag"
set_env SAFETY_DB_NAME "safety"
set_env PEDASHOP_DB_NAME "pedashop"
set_env SYSTEM_MANAGER_DB_NAME "system_manager"
set_env TPMANAGER_DB_NAME "tpmanager"
set_env PFMP_DB_NAME "pfmp"
set_env LP_CORE_ADMIN_USERNAME "$ADMIN_USER_ARG"
set_env LP_CORE_ADMIN_PASSWORD "$ADMIN_PASS_ARG"
set_env RUN_MIGRATIONS "1"
set_env LOAD_DEMO_DATA "$LOAD_DEMO_ARG"
set_env LP_CORE_DEMO_XLSX "/imports/base_demo_lp_core.xlsx"
set_env ENABLE_DB_SUPERVISION "1"
set_env CHECKSUM_VERIFY_ON_INSTALL "1"
set_env BACKUP_PRE_UPGRADE_REQUIRED "${BACKUP_PRE_UPGRADE_REQUIRED:-1}"
set_env SUITE_HOST_ROOT "$(pwd)"
validate_env

if [ "$CONFIG_MODE" = "install" ]; then
  echo "Configuration .env mise à jour : PostgreSQL + admin ${ADMIN_USER_ARG}. Démo=${LOAD_DEMO_ARG}."
else
  echo "Configuration .env mise à jour : PostgreSQL + admin ${ADMIN_USER_ARG}. Démo désactivée en mode ${CONFIG_MODE}."
fi
RC2EOF
chmod +x scripts/configure_install_env.sh

write_file pfmp-app/docker-entrypoint.sh <<'RC2EOF'
#!/usr/bin/env bash
set -e

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec gunicorn pfmp_project.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
RC2EOF
chmod +x pfmp-app/docker-entrypoint.sh

write_file scripts/postgres/db_common.sh <<'RC2EOF'
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
SUITE_ROOT="$(pwd)"

env_get(){
  local key="$1" default="${2:-}"
  local value=""
  if [ -f .env ]; then
    value="$(awk -F= -v k="$key" '$1==k{print substr($0,index($0,"=")+1)}' .env | tail -n 1)"
  fi
  printf '%s' "${value:-$default}"
}

dc(){ docker compose --env-file .env "$@"; }

POSTGRES_SERVICE="$(env_get POSTGRES_SERVICE postgres)"
POSTGRES_USER="$(env_get POSTGRES_USER lp_suite_user)"
POSTGRES_DB="$(env_get POSTGRES_DB lp_core)"
POSTGRES_PASSWORD="$(env_get POSTGRES_PASSWORD '')"

MODULES=(lp-core toolmag safety pedashop system-manager tpmanager pfmp)

module_db(){
  case "$1" in
    lp-core|core|lp_core|lp-core-app) echo "$(env_get LP_CORE_DB_NAME lp_core)" ;;
    toolmag|toolmag-app) echo "$(env_get TOOLMAG_DB_NAME toolmag)" ;;
    safety|safety-app|safety-manager) echo "$(env_get SAFETY_DB_NAME safety)" ;;
    pedashop|pedashop-app) echo "$(env_get PEDASHOP_DB_NAME pedashop)" ;;
    system-manager|system|system-manager-app) echo "$(env_get SYSTEM_MANAGER_DB_NAME system_manager)" ;;
    tpmanager|tp|tp-manager|tpmanager-app) echo "$(env_get TPMANAGER_DB_NAME tpmanager)" ;;
    pfmp|pfmp-app|pfmp-manager) echo "$(env_get PFMP_DB_NAME pfmp)" ;;
    *) return 1 ;;
  esac
}

norm_module(){
  case "$1" in
    all|total|toutes|tous) echo all ;;
    lp-core|core|lp_core|lp-core-app) echo lp-core ;;
    toolmag|toolmag-app) echo toolmag ;;
    safety|safety-app|safety-manager) echo safety ;;
    pedashop|pedashop-app) echo pedashop ;;
    system-manager|system|system-manager-app) echo system-manager ;;
    tpmanager|tp|tp-manager|tpmanager-app) echo tpmanager ;;
    pfmp|pfmp-app|pfmp-manager) echo pfmp ;;
    *) return 1 ;;
  esac
}

module_service(){
  case "$1" in
    lp-core) echo lp-core-app ;;
    toolmag) echo toolmag-app ;;
    safety) echo safety-app ;;
    pedashop) echo pedashop-app ;;
    system-manager) echo system-manager-app ;;
    tpmanager) echo tpmanager-app ;;
    pfmp) echo pfmp-app ;;
    *) return 1 ;;
  esac
}

ensure_postgres(){
  dc up -d "$POSTGRES_SERVICE" >/dev/null
  dc exec -T "$POSTGRES_SERVICE" pg_isready -U "$POSTGRES_USER" -d "${POSTGRES_DB:-lp_core}" >/dev/null
}

safe_db_name(){
  case "$1" in
    *[!a-zA-Z0-9_-]*|'') echo "Nom de base interdit: $1" >&2; return 1 ;;
    *) return 0 ;;
  esac
}

pg_exec(){
  dc exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_SERVICE" "$@"
}

create_db_if_missing(){
  local db="$1"
  safe_db_name "$db"
  pg_exec sh -lc "psql -U '$POSTGRES_USER' -d postgres -tAc \"SELECT 1 FROM pg_database WHERE datname='$db'\" | grep -q 1 || createdb -U '$POSTGRES_USER' '$db'"
}
RC2EOF
chmod +x scripts/postgres/db_common.sh

write_file scripts/postgres/ensure_databases.sh <<'RC2EOF'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/db_common.sh"

MODULE="${1:-all}"
MODULE="$(norm_module "$MODULE")" || { echo "Module inconnu: $MODULE" >&2; exit 1; }
ensure_postgres

if [ "$MODULE" = "all" ]; then
  for module in "${MODULES[@]}"; do
    db="$(module_db "$module")"
    echo "Vérification base PostgreSQL: $module -> $db"
    create_db_if_missing "$db"
  done
else
  db="$(module_db "$MODULE")"
  echo "Vérification base PostgreSQL: $MODULE -> $db"
  create_db_if_missing "$db"
fi
RC2EOF
chmod +x scripts/postgres/ensure_databases.sh

write_file scripts/full_backup.sh <<'RC2EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
SUITE_ROOT="$(pwd)"
MODE="${1:-manual}"

need(){ command -v "$1" >/dev/null 2>&1 || { echo "ERREUR : commande absente : $1" >&2; exit 1; }; }
need docker
need zip
need sha256sum
if ! docker compose version >/dev/null 2>&1; then echo "ERREUR : Docker Compose v2 indisponible." >&2; exit 1; fi

env_get(){
  local key="$1" default="${2:-}"
  local value=""
  if [ -f .env ]; then
    value="$(awk -F= -v k="$key" '$1==k{print substr($0,index($0,"=")+1)}' .env | tail -n 1)"
  fi
  printf '%s' "${value:-$default}"
}

RETENTION_DAYS="$(env_get BACKUP_RETENTION_DAYS 7)"
if [ -f lp-core-db/data/backup-policy.env ]; then
  p="$(awk -F= '$1=="BACKUP_RETENTION_DAYS"{print $2}' lp-core-db/data/backup-policy.env | tail -n1)"
  RETENTION_DAYS="${p:-$RETENTION_DAYS}"
fi
STAMP="$(date +%Y%m%d-%H%M%S)"
case "$MODE" in
  daily) BACKUP_DIR="$SUITE_ROOT/backups/daily" ;;
  pre-upgrade|pre_upgrade) BACKUP_DIR="$SUITE_ROOT/backups/pre_upgrade" ;;
  pre-restore|pre_restore) BACKUP_DIR="$SUITE_ROOT/backups/pre_restore" ;;
  *) BACKUP_DIR="$SUITE_ROOT/backups/manual" ;;
esac
mkdir -p "$BACKUP_DIR" "$SUITE_ROOT/backups/tmp"
TMP="$(mktemp -d "$SUITE_ROOT/backups/tmp/full-backup-$STAMP-XXXX")"
ARCHIVE="$BACKUP_DIR/lp-suite-full-$STAMP.zip"
trap 'rm -rf "$TMP"' EXIT

copy_if_exists(){
  local src="$1"
  if [[ -e "$SUITE_ROOT/$src" ]]; then
    mkdir -p "$TMP/$(dirname "$src")"
    cp -a "$SUITE_ROOT/$src" "$TMP/$src"
  fi
}
copy_if_exists ".env"
copy_if_exists "docker-compose.yml"
copy_if_exists "README.md"
copy_if_exists "docs"
for d in lp-core-db toolmag-db safety-db pedashop-db system-manager-db tpmanager-db pfmp-db media uploads ssl imports logs; do
  copy_if_exists "$d"
done

if [[ -x "$SUITE_ROOT/scripts/postgres/export_database_dumps.sh" ]]; then
  "$SUITE_ROOT/scripts/postgres/export_database_dumps.sh" "$TMP" all || echo "Avertissement : export PostgreSQL impossible." >&2
fi

cat > "$TMP/manifest.json" <<BACKUP_MANIFEST_EOF
{
  "suite": "lp-gestion-atelier-ep-suite",
  "backup_type": "full",
  "created_at": "$(date -Iseconds)",
  "mode": "$MODE",
  "retention_days": $RETENTION_DAYS,
  "hostname": "$(hostname)",
  "suite_root": "$SUITE_ROOT",
  "contains": ["env", "postgresql_dumps", "media", "uploads", "ssl", "imports", "logs", "metadata"],
  "restore_note": "Installer une version neuve compatible, puis restaurer cette archive depuis LP Core > Sauvegardes."
}
BACKUP_MANIFEST_EOF
(
  cd "$TMP"
  find . -type f ! -name checksums.sha256 -print0 | sort -z | xargs -0 sha256sum > checksums.sha256
  zip -qr "$ARCHIVE" .
)
rm -rf "$TMP"
trap - EXIT
if [[ "$MODE" == "daily" ]]; then
  find "$BACKUP_DIR" -type f -name 'lp-suite-full-*.zip' -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true
fi
echo "Sauvegarde complète créée : $ARCHIVE"
RC2EOF
chmod +x scripts/full_backup.sh

write_file scripts/load_demo_data.sh <<'RC2EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

FROM_INSTALL=0
if [ "${1:-}" = "--from-install" ]; then FROM_INSTALL=1; fi

log(){ echo "[$(date +%H:%M:%S)] $*"; }
dc(){ docker compose --env-file .env "$@"; }
run_manage(){ local service="$1"; shift; dc run --rm --no-deps "$service" python manage.py "$@"; }
exec_manage(){ local service="$1"; shift; dc exec -T "$service" python manage.py "$@"; }

if ! docker compose version >/dev/null 2>&1; then
  echo "ERREUR : Docker Compose v2 n'est pas disponible." >&2
  exit 1
fi

log "Chargement des données de démonstration LP Suite."
log "Usage normal : appelé automatiquement uniquement par ./install.sh --mode install si la démo a été acceptée."
log "Les commandes sont tolérantes : un module absent ou une seed absente ne bloque pas l'ensemble."

if [ -f imports/base_demo_lp_core.xlsx ]; then
  log "LP Core : import imports/base_demo_lp_core.xlsx"
  run_manage lp-core-app import_users_xlsx /imports/base_demo_lp_core.xlsx || true
fi

log "LP Core : seed_core de consolidation"
ADMIN_USER="$(awk -F= '$1=="LP_CORE_ADMIN_USERNAME"{print substr($0,index($0,"=")+1)}' .env | tail -n1)"
ADMIN_PASS="$(awk -F= '$1=="LP_CORE_ADMIN_PASSWORD"{print substr($0,index($0,"=")+1)}' .env | tail -n1)"
if [ -n "${ADMIN_PASS:-}" ]; then
  run_manage lp-core-app seed_core --admin-username "${ADMIN_USER:-admin}" --admin-password "$ADMIN_PASS" || true
else
  run_manage lp-core-app seed_core || true
fi

log "ToolMag : référentiels et démo"
run_manage toolmag-app seed_referentials || true
run_manage toolmag-app seed_demo || true
log "Safety Manager : démo / référentiels"
run_manage safety-app seed_safety_manager || true
log "PedaShop : démo / référentiels"
run_manage pedashop-app seed_pedashop || true
log "System Manager : démo / référentiels"
run_manage system-manager-app seed_system_manager || true
log "TP Manager : démo / référentiels"
run_manage tpmanager-app seed_tp_manager || true
run_manage tpmanager-app seed_tpmanager_v2 || true
run_manage tpmanager-app seed_sequence_manager || true
run_manage tpmanager-app seed_evaluation_demo || true
log "PFMP Manager : démo / référentiels"
run_manage pfmp-app seed_pfmp_manager || true

log "Synchronisation post-démo vers les modules"
for svc in toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app; do
  exec_manage "$svc" sync_lp_core_users || true
done
log "Chargement démo terminé."
RC2EOF
chmod +x scripts/load_demo_data.sh

write_file scripts/collectstatic_module.sh <<'RC2EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/postgres/db_common.sh
MODULE="$(norm_module "${1:-all}")" || { echo "Module inconnu: ${1:-}" >&2; exit 1; }
collect_one(){
  local module="$1" service
  service="$(module_service "$module")"
  dc up -d "$service" >/dev/null
  echo "Collectstatic : $service"
  dc exec -T "$service" python manage.py collectstatic --noinput
}
if [ "$MODULE" = "all" ]; then for m in "${MODULES[@]}"; do collect_one "$m"; done; else collect_one "$MODULE"; fi
RC2EOF
chmod +x scripts/collectstatic_module.sh

write_file scripts/sync_module_users.sh <<'RC2EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/postgres/db_common.sh
MODULE="$(norm_module "${1:-all}")" || { echo "Module inconnu: ${1:-}" >&2; exit 1; }
sync_one(){
  local module="$1" service
  [ "$module" = "lp-core" ] && return 0
  service="$(module_service "$module")"
  dc up -d "$service" >/dev/null
  echo "Synchronisation LP Core -> $service"
  dc exec -T "$service" python manage.py sync_lp_core_users
}
if [ "$MODULE" = "all" ]; then for m in toolmag safety pedashop system-manager tpmanager pfmp; do sync_one "$m"; done; else sync_one "$MODULE"; fi
RC2EOF
chmod +x scripts/sync_module_users.sh

write_file scripts/restart_module.sh <<'RC2EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/postgres/db_common.sh
MODULE="$(norm_module "${1:-all}")" || { echo "Module inconnu: ${1:-}" >&2; exit 1; }
if [ "$MODULE" = "all" ]; then
  dc restart lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app lp-gateway
else
  service="$(module_service "$MODULE")"
  dc restart "$service"
fi
RC2EOF
chmod +x scripts/restart_module.sh

write_file scripts/logs_module.sh <<'RC2EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/postgres/db_common.sh
MODULE="$(norm_module "${1:-all}")" || { echo "Module inconnu: ${1:-}" >&2; exit 1; }
LINES="${2:-160}"
if [ "$MODULE" = "all" ]; then
  dc logs --tail="$LINES" lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app lp-gateway
else
  service="$(module_service "$MODULE")"
  dc logs --tail="$LINES" "$service"
fi
RC2EOF
chmod +x scripts/logs_module.sh

write_file scripts/migrate_all.sh <<'RC2EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. scripts/postgres/db_common.sh

MODULE="all"
RUN_SEEDS=1
RUN_STATIC=1
usage(){
  cat <<'HELP'
Usage : ./scripts/migrate_all.sh [--module <module>] [--skip-seed] [--skip-static]
Modules : all, lp-core, toolmag, safety, pedashop, system-manager, tpmanager, pfmp
HELP
}
while [ $# -gt 0 ]; do
  case "$1" in
    --module) MODULE="${2:-}"; shift 2;;
    --skip-seed) RUN_SEEDS=0; shift;;
    --skip-static) RUN_STATIC=0; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Option inconnue : $1" >&2; usage >&2; exit 1;;
  esac
done
log(){ echo "[$(date +%H:%M:%S)] $*"; }
service_exists(){ dc config --services 2>/dev/null | grep -qx "$1"; }
service_running(){ [ -n "$(dc ps -q "$1" 2>/dev/null || true)" ]; }
exec_manage(){
  local service="$1"; shift
  if service_exists "$service" && service_running "$service"; then
    dc exec -T "$service" python manage.py "$@"
  else
    log "Service absent ou non démarré, étape ignorée : $service $*"
  fi
}
run_migrate(){
  local service="$1" module="$2"
  create_db_if_missing "$(module_db "$module")"
  if service_exists "$service"; then
    if ! service_running "$service"; then
      log "Démarrage du service pour migrations : $service"
      dc up -d "$service"
    fi
    log "Migrations Django : $service"
    exec_manage "$service" migrate --noinput
    if [ "$RUN_STATIC" = "1" ]; then exec_manage "$service" collectstatic --noinput || true; fi
  else
    log "Service non défini dans docker-compose : $service"
  fi
}
MODULE="$(norm_module "$MODULE")"
run_module(){
  local module="$1" service
  service="$(module_service "$module")"
  run_migrate "$service" "$module"
  if [ "$RUN_SEEDS" = "1" ]; then
    case "$module" in
      lp-core) ;;
      toolmag) exec_manage toolmag-app sync_lp_core_users || true ;;
      safety) exec_manage safety-app sync_lp_core_users || true; exec_manage safety-app seed_safety_manager || true ;;
      pedashop) exec_manage pedashop-app sync_lp_core_users || true; exec_manage pedashop-app seed_pedashop || true; exec_manage pedashop-app pedashop_recalculate_stock_alerts || true; exec_manage pedashop-app pedashop_check_integrity || true ;;
      system-manager) exec_manage system-manager-app sync_lp_core_users || true; exec_manage system-manager-app seed_system_manager || true ;;
      tpmanager) exec_manage tpmanager-app sync_lp_core_users || true; exec_manage tpmanager-app sync_system_manager || true; exec_manage tpmanager-app seed_tp_manager || true; exec_manage tpmanager-app seed_tpmanager_v2 || true; exec_manage tpmanager-app seed_sequence_manager || true ;;
      pfmp) exec_manage pfmp-app sync_lp_core_users || true; exec_manage pfmp-app seed_pfmp_manager || true ;;
    esac
  fi
}
ensure_postgres
if [ "$MODULE" = "all" ]; then
  for m in "${MODULES[@]}"; do run_module "$m"; done
else
  run_module "$MODULE"
fi
log "Migrations terminées. Module : $MODULE"
RC2EOF
chmod +x scripts/migrate_all.sh

write_file install.sh <<'RC2EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
trap 'echo; echo "Installation interrompue." >&2; exit 130' INT TERM
cd "$(dirname "$0")"

MODE="auto"
FULL_REBUILD=0
CLEAN_BUILD=0
SKIP_SEED=0
SKIP_MIGRATIONS=0
YES=0
SKIP_CHECKSUM=0
FORCE_DEMO=""
usage(){
  cat <<'HELP'
Usage : ./install.sh [options]
Modes : --mode install | update | upgrade | auto
Options : --full-rebuild --clean-build --skip-seed --skip-migrations --demo --no-demo --skip-checksum -y|--yes
HELP
}
while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="$2"; shift 2;;
    --mode=*) MODE="${1#*=}"; shift;;
    --full-rebuild) FULL_REBUILD=1; shift;;
    --clean-build) CLEAN_BUILD=1; FULL_REBUILD=1; shift;;
    --skip-seed) SKIP_SEED=1; shift;;
    --skip-migrations) SKIP_MIGRATIONS=1; shift;;
    --demo) FORCE_DEMO=1; shift;;
    --no-demo) FORCE_DEMO=0; shift;;
    --skip-checksum) SKIP_CHECKSUM=1; shift;;
    -y|--yes) YES=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Option inconnue : $1" >&2; usage >&2; exit 1;;
  esac
done
log(){ echo "[$(date +%H:%M:%S)] $*"; }
need(){ command -v "$1" >/dev/null 2>&1 || { echo "ERREUR : commande absente : $1" >&2; exit 1; }; }
need docker; need python3; need awk
if ! docker compose version >/dev/null 2>&1; then echo "ERREUR : Docker Compose v2 n'est pas disponible." >&2; exit 1; fi
[ -f .env ] || cp .env.example .env
dc(){ docker compose --env-file .env "$@"; }
env_get(){ awk -F= -v k="$1" '$1==k{print substr($0,index($0,"=")+1)}' .env | tail -n 1; }
validate_env(){
  python3 - <<'PY'
from pathlib import Path
import re
bad=[]
for i,line in enumerate(Path('.env').read_text(encoding='utf-8').splitlines(),1):
    s=line.strip()
    if not s or s.startswith('#'): continue
    if '=' not in s:
        bad.append((i,line,"ligne sans '='")); continue
    k=s.split('=',1)[0]
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', k): bad.append((i,line,'clé invalide'))
if bad:
    for i,line,why in bad: print(f'.env invalide ligne {i}: {why}: {line!r}')
    raise SystemExit(1)
PY
}
if [ "$SKIP_CHECKSUM" = "0" ] && [ -f CHECKSUMS.sha256 ]; then
  CHECKSUM_ON="${CHECKSUM_VERIFY_ON_INSTALL:-1}"
  if [ -f .env ]; then CHECKSUM_ON="$(env_get CHECKSUM_VERIFY_ON_INSTALL || true)"; fi
  CHECKSUM_ON="${CHECKSUM_ON:-1}"
  if [ "$CHECKSUM_ON" = "1" ] && [ -x scripts/verify_checksums.sh ]; then
    log "Vérification intégrité archive : CHECKSUMS.sha256"
    scripts/verify_checksums.sh --quiet
  fi
fi
CURRENT_VERSION="unknown"
[ -f .suite-version ] && CURRENT_VERSION="$(cat .suite-version | head -1 | tr -d '\r\n')"
[ -f VERSION ] && NEW_VERSION="$(cat VERSION | head -1 | tr -d '\r\n')" || NEW_VERSION="unknown"
if [ "$MODE" = "auto" ]; then if [ ! -f .suite-version ]; then MODE="install"; else MODE="update"; fi; fi
case "$MODE" in install|update|upgrade) ;; *) echo "Mode invalide : $MODE" >&2; exit 1;; esac
if [ "$MODE" != "install" ] && [ -n "$FORCE_DEMO" ]; then echo "ERREUR : --demo/--no-demo réservés au mode install." >&2; exit 1; fi
log "Mode sélectionné : $MODE"
log "Version installée : $CURRENT_VERSION"
log "Version archive/code : $NEW_VERSION"
python3 scripts/check_version_policy.py "$MODE" "$CURRENT_VERSION"
CONFIGURE_ENV_ARGS=(--mode "$MODE")
if [ "$MODE" = "install" ] && [ -n "$FORCE_DEMO" ]; then [ "$FORCE_DEMO" = "1" ] && CONFIGURE_ENV_ARGS+=(--demo) || CONFIGURE_ENV_ARGS+=(--no-demo); fi
if [ "$MODE" = "install" ]; then
  ./scripts/configure_install_env.sh "${CONFIGURE_ENV_ARGS[@]}"
else
  if grep -q '^POSTGRES_PASSWORD=CHANGE_ME' .env || ! grep -q '^POSTGRES_PASSWORD=' .env; then
    log "Mot de passe PostgreSQL absent ou générique : configuration interactive requise."
    ./scripts/configure_install_env.sh "${CONFIGURE_ENV_ARGS[@]}"
  else
    ./scripts/set_env_value.sh LOAD_DEMO_DATA 0
  fi
fi
if [ -x ./scripts/configure_public_urls.sh ]; then
  if [ "$MODE" = "install" ]; then
    echo "Configuration des adresses publiques. Pour un test local : localhost."
    ./scripts/configure_public_urls.sh
  elif [ "$YES" = "0" ]; then
    read -rp "Conserver les URL/ports actuels du .env ? [O/n] : " keep_urls
    if [[ "${keep_urls:-O}" =~ ^[Nn]$ ]]; then ./scripts/configure_public_urls.sh; fi
  fi
fi
validate_env
mkdir -p postgres-db/data lp-core-db/data toolmag-db/data safety-db/data pedashop-db/data system-manager-db/data tpmanager-db/data pfmp-db/data \
  lp-core-db/data/staticfiles toolmag-db/data/staticfiles safety-db/data/staticfiles pedashop-db/data/staticfiles system-manager-db/data/staticfiles tpmanager-db/data/staticfiles pfmp-db/data/staticfiles \
  lp-core-db/data/updates/incoming lp-core-db/data/updates/logs backups/daily backups/manual backups/pre_upgrade backups/tmp imports logs updates/incoming updates/logs ssl
BACKUP_REQUIRED="$(env_get BACKUP_PRE_UPGRADE_REQUIRED)"; BACKUP_REQUIRED="${BACKUP_REQUIRED:-1}"
if [ "$MODE" != "install" ] && [ "$BACKUP_REQUIRED" = "1" ]; then
  log "Sauvegarde pré-${MODE} requise."
  scripts/full_backup.sh pre-upgrade
fi
log "Arrêt des conteneurs existants, volumes conservés."
dc down --remove-orphans || true
if [ "$CLEAN_BUILD" = "1" ]; then
  log "Nettoyage Docker sécurisé : cache BuildKit/images inutilisées, volumes conservés."
  docker builder prune -af || true
  docker system prune -f || true
fi
log "Démarrage PostgreSQL."
dc up -d postgres
log "Attente PostgreSQL."
PGUSER="$(env_get POSTGRES_USER)"; PGUSER="${PGUSER:-lp_suite_user}"
for i in $(seq 1 60); do
  if dc exec -T postgres pg_isready -U "$PGUSER" >/dev/null 2>&1; then break; fi
  sleep 2
  if [ "$i" = "60" ]; then echo "ERREUR : PostgreSQL ne répond pas." >&2; exit 1; fi
done
log "Vérification/création des bases PostgreSQL."
scripts/postgres/ensure_databases.sh all
BUILD_ARGS=(); [ "$FULL_REBUILD" = "1" ] && BUILD_ARGS+=(--no-cache)
BUILD_SERVICES=(lp-gateway lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app suite-admin-agent suite-backup-scheduler)
log "Construction des images."
dc build "${BUILD_ARGS[@]}" "${BUILD_SERVICES[@]}"
run_app(){ dc run --rm --no-deps "$@"; }
seed_app(){ if [ "$SKIP_SEED" = "1" ]; then log "Seed ignoré : $*"; else run_app "$@"; fi; }
run_manage(){ local service="$1"; shift; run_app "$service" python manage.py "$@"; }
if [ "$SKIP_MIGRATIONS" = "0" ]; then
  log "Migrations et initialisation LP Core."
  run_manage lp-core-app migrate --noinput
  run_manage lp-core-app collectstatic --noinput
  ADMIN_USER="$(env_get LP_CORE_ADMIN_USERNAME)"; ADMIN_USER="${ADMIN_USER:-admin}"
  ADMIN_PASS="$(env_get LP_CORE_ADMIN_PASSWORD)"
  seed_app lp-core-app python manage.py seed_core --admin-username "$ADMIN_USER" --admin-password "$ADMIN_PASS"
  if [ -n "$(env_get LP_CORE_IMPORT_XLSX)" ]; then
    IMPORT_XLSX="$(env_get LP_CORE_IMPORT_XLSX)"
    log "Import Excel LP Core : $IMPORT_XLSX"
    run_manage lp-core-app import_users_xlsx "$IMPORT_XLSX" || true
  fi
  for svc in toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app; do
    log "Migrations : $svc"
    run_manage "$svc" migrate --noinput
    run_manage "$svc" collectstatic --noinput || true
  done
  seed_app safety-app python manage.py seed_safety_manager || true
  seed_app pedashop-app python manage.py seed_pedashop || true
  seed_app system-manager-app python manage.py seed_system_manager || true
  seed_app tpmanager-app python manage.py seed_tp_manager || true
  seed_app tpmanager-app python manage.py seed_tpmanager_v2 || true
  seed_app tpmanager-app python manage.py seed_sequence_manager || true
  seed_app pfmp-app python manage.py seed_pfmp_manager || true
  if [ "$MODE" = "install" ]; then
    LOAD_DEMO="$(env_get LOAD_DEMO_DATA)"; LOAD_DEMO="${LOAD_DEMO:-0}"
    if [ "$LOAD_DEMO" = "1" ]; then
      log "Chargement automatique des bases de démonstration demandé à l'installation."
      [ -x scripts/load_demo_data.sh ] && scripts/load_demo_data.sh --from-install || true
    else
      log "Bases de démonstration non chargées pour cette installation."
    fi
  else
    log "Mode $MODE : bases de démonstration non chargées automatiquement."
  fi
else
  log "Migrations ignorées sur demande (--skip-migrations)."
fi
log "Démarrage final des services."
dc up -d lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app suite-admin-agent suite-backup-scheduler lp-gateway
log "Synchronisations LP Core après démarrage."
for svc in toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app; do
  dc exec -T "$svc" python manage.py sync_lp_core_users || true
done
dc exec -T tpmanager-app python manage.py sync_system_manager || true
[ -x ./scripts/verify_portal_routes.sh ] && ./scripts/verify_portal_routes.sh || true
printf '%s\n' "$NEW_VERSION" > .suite-version
log "Installation/mise à jour terminée."
echo "Portail : $(env_get LP_CORE_PUBLIC_URL)"
echo "Compte admin LP Core : $(env_get LP_CORE_ADMIN_USERNAME) / mot de passe choisi à l'installation"
echo "Version enregistrée : $NEW_VERSION"
RC2EOF
chmod +x install.sh

python3 - <<'PY'
from pathlib import Path
p = Path('suite-admin-agent/agent.py')
text = p.read_text(encoding='utf-8')
text = text.replace("'restart_services': ['docker', 'compose', 'up', '-d', '--build'],", "'restart_services': ['docker', 'compose', '--env-file', '.env', 'up', '-d', '--build'],")
text = text.replace("'migrate_all': ['bash', str(SUITE_ROOT / 'scripts/migrate_all.sh')],", "'migrate_all': ['bash', str(SUITE_ROOT / 'scripts/migrate_all.sh')],\n        'sync_all_modules': ['bash', str(SUITE_ROOT / 'scripts/sync_module_users.sh'), 'all'],\n        'collectstatic_all': ['bash', str(SUITE_ROOT / 'scripts/collectstatic_module.sh'), 'all'],")
marker = "    if action == 'backup_database':\n"
insert = """    if action in {'migrate_module', 'collectstatic_module', 'sync_module', 'restart_module', 'logs_module'}:\n        module = str(payload.get('module') or 'all')\n        allowed_modules = {'all','lp-core','toolmag','safety','pedashop','system-manager','tpmanager','pfmp'}\n        if module not in allowed_modules:\n            raise ValueError('Module non autorisé.')\n        if action == 'migrate_module':\n            command = ['bash', str(SUITE_ROOT / 'scripts/migrate_all.sh'), '--module', module, '--skip-seed']\n        elif action == 'collectstatic_module':\n            command = ['bash', str(SUITE_ROOT / 'scripts/collectstatic_module.sh'), module]\n        elif action == 'sync_module':\n            command = ['bash', str(SUITE_ROOT / 'scripts/sync_module_users.sh'), module]\n        elif action == 'restart_module':\n            command = ['bash', str(SUITE_ROOT / 'scripts/restart_module.sh'), module]\n        else:\n            command = ['bash', str(SUITE_ROOT / 'scripts/logs_module.sh'), module, '180']\n    elif action == 'backup_database':\n"""
if marker in text and "action in {'migrate_module'" not in text:
    text = text.replace(marker, insert)
p.write_text(text, encoding='utf-8')
PY

python3 - <<'PY'
from pathlib import Path
p = Path('lp-core-app/core/views.py')
text = p.read_text(encoding='utf-8')
old = """def database_supervision_view(request):\n    from django.contrib import messages\n    from django.shortcuts import redirect\n    if not _core_sql_admin_user(request):\n        messages.error(request, 'Accès réservé administrateur LP Core.')\n        return redirect('core_login')\n    from .db_supervision import collect_database_supervision\n    context = collect_database_supervision()\n    return render(request, 'core/database_supervision.html', context)\n"""
new = """@require_http_methods(['GET', 'POST'])\ndef database_supervision_view(request):\n    from django.contrib import messages\n    from django.shortcuts import redirect\n    actor = _core_sql_admin_user(request)\n    if not actor:\n        messages.error(request, 'Accès réservé administrateur LP Core.')\n        return redirect('core_login')\n    if request.method == 'POST':\n        form_action = request.POST.get('form_action') or ''\n        module = request.POST.get('module') or 'all'\n        allowed_modules = {'all','lp-core','toolmag','safety','pedashop','system-manager','tpmanager','pfmp'}\n        action_map = {\n            'migrate_module': 'migrate_module',\n            'collectstatic_module': 'collectstatic_module',\n            'sync_module': 'sync_module',\n            'sync_all_modules': 'sync_all_modules',\n            'restart_module': 'restart_module',\n            'logs_module': 'logs_module',\n            'restart_services': 'restart_services',\n        }\n        if module not in allowed_modules:\n            messages.error(request, 'Module non autorisé.')\n            return redirect('core_database_supervision')\n        agent_action = action_map.get(form_action)\n        if not agent_action:\n            messages.error(request, 'Action supervision inconnue.')\n            return redirect('core_database_supervision')\n        payload = {'module': module}\n        job, data = _record_agent_job(agent_action, actor, payload=payload, success_message=f'Action {agent_action} demandée pour {module}.')\n        if data.get('ok'):\n            messages.success(request, f'Action lancée : {agent_action} / {module} — job {job.agent_job_id}.')\n        else:\n            messages.error(request, job.result_message or 'Action refusée par l’agent serveur.')\n        return redirect('core_database_supervision')\n    from .db_supervision import collect_database_supervision\n    context = collect_database_supervision()\n    context['supervision_modules'] = DATABASE_BACKUP_MODULES\n    return render(request, 'core/database_supervision.html', context)\n"""
if old not in text:
    raise SystemExit('Bloc database_supervision_view introuvable')
p.write_text(text.replace(old, new), encoding='utf-8')
PY

write_file lp-core-app/core/templates/core/database_supervision.html <<'RC2EOF'
{% extends 'core/base.html' %}

{% block content %}
<section class="card">
  <h1>Supervision des bases PostgreSQL</h1>
  <p class="muted">Vue de contrôle rapide depuis LP Core : état des bases de chaque module, taille, nombre de tables, dernière migration Django connue et actions de maintenance contrôlées par l’agent serveur.</p>

  <div class="cards compact">
    <article><strong>Moteur</strong><br><code>{{ engine }}</code></article>
    <article><strong>Hôte PostgreSQL</strong><br><code>{{ host }}:{{ port }}</code></article>
    <article><strong>Utilisateur</strong><br><code>{{ user }}</code></article>
    <article><strong>État</strong><br>{{ ok_count }} / {{ total_count }} base(s) accessibles</article>
  </div>

  <div class="panel">
    <h2>Actions globales</h2>
    <form method="post" style="display:inline">{% csrf_token %}<input type="hidden" name="form_action" value="migrate_module"><input type="hidden" name="module" value="all"><button type="submit">Relancer toutes les migrations</button></form>
    <form method="post" style="display:inline">{% csrf_token %}<input type="hidden" name="form_action" value="collectstatic_module"><input type="hidden" name="module" value="all"><button type="submit">Relancer tous les collectstatic</button></form>
    <form method="post" style="display:inline">{% csrf_token %}<input type="hidden" name="form_action" value="sync_all_modules"><input type="hidden" name="module" value="all"><button type="submit">Synchroniser LP Core vers tous les modules</button></form>
    <form method="post" style="display:inline">{% csrf_token %}<input type="hidden" name="form_action" value="restart_services"><input type="hidden" name="module" value="all"><button type="submit">Redémarrer la suite</button></form>
  </div>

  {% if not postgres_mode %}
    <p class="alert warning">Installation actuellement en SQLite : la supervision multi-bases complète sera disponible après bascule PostgreSQL.</p>
  {% endif %}

  <table>
    <tr>
      <th>Module</th><th>Base</th><th>État</th><th>Taille</th><th>Tables</th><th>Migrations</th><th>Dernière migration</th><th>Actions</th><th>Détail</th>
    </tr>
    {% for db in items %}
    <tr>
      <td><strong>{{ db.label }}</strong><br><small>{{ db.code }}</small></td>
      <td><code>{{ db.database }}</code></td>
      <td>{% if db.ok %}<span class="badge success">OK</span>{% else %}<span class="badge danger">Erreur</span>{% endif %}</td>
      <td>{{ db.size_pretty }}</td>
      <td>{{ db.table_count|default:'—' }}</td>
      <td>{{ db.migration_count|default:'—' }}</td>
      <td><code>{{ db.last_migration }}</code></td>
      <td>
        <form method="post" style="display:inline">{% csrf_token %}<input type="hidden" name="module" value="{{ db.code }}"><input type="hidden" name="form_action" value="migrate_module"><button type="submit">Migrations</button></form>
        <form method="post" style="display:inline">{% csrf_token %}<input type="hidden" name="module" value="{{ db.code }}"><input type="hidden" name="form_action" value="collectstatic_module"><button type="submit">Static</button></form>
        {% if db.code != 'lp-core' %}<form method="post" style="display:inline">{% csrf_token %}<input type="hidden" name="module" value="{{ db.code }}"><input type="hidden" name="form_action" value="sync_module"><button type="submit">Sync</button></form>{% endif %}
        <form method="post" style="display:inline">{% csrf_token %}<input type="hidden" name="module" value="{{ db.code }}"><input type="hidden" name="form_action" value="restart_module"><button type="submit">Restart</button></form>
        <form method="post" style="display:inline">{% csrf_token %}<input type="hidden" name="module" value="{{ db.code }}"><input type="hidden" name="form_action" value="logs_module"><button type="submit">Logs</button></form>
      </td>
      <td>{% if db.error %}<pre class="mini-pre">{{ db.error }}</pre>{% else %}<span class="muted">—</span>{% endif %}</td>
    </tr>
    {% endfor %}
  </table>

  <div class="panel">
    <h2>Commandes utiles côté serveur</h2>
    <pre class="mini-pre">docker compose --env-file .env ps
docker exec -it lp-suite-postgres pg_isready -U lp_suite_user -d lp_core
docker compose --env-file .env logs --tail=150 postgres</pre>
  </div>
</section>
{% endblock %}
RC2EOF

# Version RC2
printf 'V0.0.1-RC2\n' > VERSION
printf 'V0.0.1-RC2\n' > VERSION.txt
printf 'V0.0.1-RC2\n' > .suite-target-version

# Recalcul des checksums, hors fichiers runtime/données.
log "Recalcul CHECKSUMS.sha256"
find . \
  -path './.git' -prune -o \
  -path './backups' -prune -o \
  -path './postgres-db' -prune -o \
  -path './lp-core-db' -prune -o \
  -path './toolmag-db' -prune -o \
  -path './safety-db' -prune -o \
  -path './pedashop-db' -prune -o \
  -path './system-manager-db' -prune -o \
  -path './tpmanager-db' -prune -o \
  -path './pfmp-db' -prune -o \
  -path './updates' -prune -o \
  -path './logs' -prune -o \
  -path './ssl' -prune -o \
  -path './.env' -prune -o \
  -path './apply_rc2_fixes.sh' -prune -o \
  -type f -print0 | sort -z | xargs -0 sha256sum > CHECKSUMS.sha256

log "Contrôle syntaxe Bash"
bash -n install.sh
bash -n scripts/configure_install_env.sh
bash -n scripts/set_env_value.sh
bash -n scripts/full_backup.sh
bash -n scripts/load_demo_data.sh
bash -n scripts/migrate_all.sh
bash -n scripts/postgres/db_common.sh
bash -n scripts/postgres/ensure_databases.sh
bash -n scripts/collectstatic_module.sh
bash -n scripts/sync_module_users.sh
bash -n scripts/restart_module.sh
bash -n scripts/logs_module.sh
bash -n pfmp-app/docker-entrypoint.sh

log "Correctifs RC2 appliqués. Vérifie ensuite : git diff --stat puis git add/commit/push."
