#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://localhost:9000}"
check(){
  path="$1"; expected="$2"
  line=$(curl -sI "$BASE$path/" | tr -d '\r' | grep -i '^X-LP-Gateway-Module:' || true)
  echo "$path -> ${line:-PAS D ENTETE}"
  echo "$line" | grep -qi "$expected" || { echo "ERREUR: $path ne pointe pas vers $expected" >&2; exit 1; }
}
check /toolmag toolmag
check /safety safety
check /pedashop pedashop
check /system system
check /tpmanager tpmanager
check /pfmp pfmp
echo "OK: routage portail cohérent."
