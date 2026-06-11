#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  cp .env.example .env
fi
cp .env ".env.backup-before-v0.3.1-hotfix-$(date +%Y%m%d-%H%M%S)"

python3 - <<'PY'
from pathlib import Path
p=Path('.env')
text=p.read_text()
updates={
 'LP_CORE_SESSION_COOKIE_NAME':'lp_core_sessionid',
 'LP_CORE_CSRF_COOKIE_NAME':'lp_core_csrftoken',
 'SAFETY_SESSION_COOKIE_NAME':'safety_sessionid',
 'SAFETY_CSRF_COOKIE_NAME':'safety_csrftoken',
 'PEDASHOP_SESSION_COOKIE_NAME':'pedashop_sessionid',
 'PEDASHOP_CSRF_COOKIE_NAME':'pedashop_csrftoken',
 'SYSTEM_MANAGER_SESSION_COOKIE_NAME':'system_manager_sessionid',
 'SYSTEM_MANAGER_CSRF_COOKIE_NAME':'system_manager_csrftoken',
 'TPMANAGER_SESSION_COOKIE_NAME':'tpmanager_sessionid',
 'TPMANAGER_CSRF_COOKIE_NAME':'tpmanager_csrftoken',
 'PFMP_SESSION_COOKIE_NAME':'pfmp_sessionid',
 'PFMP_CSRF_COOKIE_NAME':'pfmp_csrftoken',
 'PFMP_SSO_TOKEN_MAX_AGE':'600',
 'SESSION_COOKIE_SAMESITE':'Lax',
 'CSRF_COOKIE_SAMESITE':'Lax',
 'LP_CORE_VERSION':'"LP Core — Bêta V0.3.1 hotfix"',
 'PFMP_VERSION':'"PFMP Manager — Bêta V0.3.1 hotfix"',
}
lines=text.splitlines()
seen=set()
out=[]
for line in lines:
    if '=' in line and not line.lstrip().startswith('#'):
        k=line.split('=',1)[0].strip()
        if k in updates:
            out.append(f'{k}={updates[k]}')
            seen.add(k)
        else:
            out.append(line)
    else:
        out.append(line)
for k,v in updates.items():
    if k not in seen:
        out.append(f'{k}={v}')
p.write_text('\n'.join(out)+'\n')
PY

mkdir -p pfmp-db/data

echo "Hotfix variables appliquées dans .env."
echo "Reconstruction et migrations :"
docker compose up -d --build lp-core-app pfmp-app lp-gateway
./scripts/migrate_all.sh --module lp-core
./scripts/migrate_all.sh --module pfmp

echo "Redémarrage conseillé de toute la suite pour appliquer les noms de cookies isolés :"
echo "  docker compose up -d --build"
echo "Puis vider les cookies du site ou tester en navigation privée."
