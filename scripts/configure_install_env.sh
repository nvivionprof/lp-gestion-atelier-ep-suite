#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE=".env"
[ -f "$ENV_FILE" ] || cp .env.example "$ENV_FILE"

set_env(){
  local key="$1"; shift
  local value="$*"
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s#^${key}=.*#${key}=${value}#" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}
get_env(){
  local key="$1"
  awk -F= -v k="$key" '$1==k{print substr($0,index($0,"=")+1)}' "$ENV_FILE" | tail -n 1
}
ask_secret_confirm(){
  local label="$1" var1 var2
  while true; do
    read -rsp "$label : " var1; echo
    read -rsp "Confirme $label : " var2; echo
    if [ -z "$var1" ]; then
      echo "Valeur vide interdite."
    elif [ "$var1" != "$var2" ]; then
      echo "Les deux saisies ne correspondent pas."
    else
      printf '%s' "$var1"
      return 0
    fi
  done
}
ask_text(){
  local label="$1" default="$2" value
  read -rp "$label [$default] : " value
  value="${value:-$default}"
  printf '%s' "$value"
}

ask_yes_no(){
  local label="$1" default="${2:-N}" value
  read -rp "$label [$default] : " value
  value="${value:-$default}"
  if [[ "$value" =~ ^[OoYy1]$ ]]; then printf '1'; else printf '0'; fi
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
    echo
    echo "Bases de démonstration : choix d'installation initiale"
    echo "- Oui : les données démo seront chargées automatiquement après les migrations."
    echo "- Non : l'installation restera vide/propre, sans données de démonstration."
    LOAD_DEMO_ARG="$(ask_yes_no 'Installer et charger les bases de démonstration ?' 'O')"
  fi
else
  # En update/upgrade, les données de démonstration ne sont jamais chargées
  # automatiquement, même si LOAD_DEMO_DATA valait 1 dans .env.
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

if [ "$CONFIG_MODE" = "install" ]; then
  echo "Configuration .env mise à jour : PostgreSQL + admin ${ADMIN_USER_ARG}. Démo=${LOAD_DEMO_ARG}."
else
  echo "Configuration .env mise à jour : PostgreSQL + admin ${ADMIN_USER_ARG}. Démo désactivée en mode ${CONFIG_MODE}."
fi
