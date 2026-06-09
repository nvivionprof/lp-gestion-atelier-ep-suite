#!/usr/bin/env bash
set -euo pipefail

echo "[RC7] Application : HTTPS DuckDNS + ToolMag accès inventaire/appareil + update rapide"

if [ ! -d .git ]; then
  echo "[ERREUR] Ce script doit être lancé dans le dépôt Git, pas dans le dossier d'installation extrait."
  echo "Chemin attendu : /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-git-rc2"
  exit 1
fi

python3 <<'PYCODE'
from pathlib import Path
import json
import re

VERSION = "V0.0.1-RC7"
DISPLAY = "RC V0.0.1"

EXCLUDE_CHECKSUM_DIRS = {
    '.git', 'backups', 'postgres-db',
    'lp-core-db', 'toolmag-db', 'safety-db', 'pedashop-db',
    'system-manager-db', 'tpmanager-db', 'pfmp-db',
    'updates', 'logs', '__pycache__'
}


def read(path):
    return Path(path).read_text(encoding='utf-8')


def write(path, text):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.rstrip() + "\n", encoding='utf-8')


def replace_line(text, key, value):
    pattern = re.compile(rf'^{re.escape(key)}=.*$', re.MULTILINE)
    line = f'{key}={value}'
    if pattern.search(text):
        return pattern.sub(line, text)
    return text.rstrip() + "\n" + line + "\n"

# Version suite
for f in ["VERSION", "VERSION.txt", ".suite-target-version"]:
    if Path(f).exists():
        write(f, VERSION)

if Path("manifest.json").exists():
    try:
        data = json.loads(read("manifest.json"))
        for key in ("version", "target_version", "current_version", "suite_version"):
            if key in data:
                data[key] = VERSION
        write("manifest.json", json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        text = re.sub(r"V0\.0\.1-RC\d+", VERSION, read("manifest.json"))
        write("manifest.json", text)

# .env.example : préparer HTTPS DuckDNS sans l'activer par défaut
p = Path('.env.example')
if p.exists():
    text = read(p)
    text = re.sub(r'LP_CORE_VERSION=.*', f'LP_CORE_VERSION="LP Core — {DISPLAY}"', text)
    text = re.sub(r'APP_VERSION=.*', f'APP_VERSION="ToolMag — {DISPLAY}"', text)
    text = re.sub(r'SAFETY_VERSION=.*', f'SAFETY_VERSION="Safety Manager — {DISPLAY}"', text)
    text = re.sub(r'PEDASHOP_VERSION=.*', f'PEDASHOP_VERSION="PedaShop — {DISPLAY}"', text)
    text = re.sub(r'SYSTEM_MANAGER_VERSION=.*', f'SYSTEM_MANAGER_VERSION="System Manager — {DISPLAY}"', text)
    text = re.sub(r'TPMANAGER_VERSION=.*', f'TPMANAGER_VERSION="TP Manager — {DISPLAY}"', text)
    text = re.sub(r'PFMP_VERSION=.*', f'PFMP_VERSION="PFMP Manager — {DISPLAY}"', text)
    if 'CERT_CHALLENGE_METHOD=' not in text:
        text += "\n# HTTPS / DuckDNS\nCERT_CHALLENGE_METHOD=dns_duckdns\nLETSENCRYPT_EMAIL=\nDUCKDNS_TOKEN=\n"
    if 'GATEWAY_HTTPS_PORT=' not in text:
        text = replace_line(text, 'GATEWAY_HTTPS_PORT', '9443')
    write(p, text)

# ToolMag : supprimer les deux boutons d'accès direct sortie/retour du tableau de bord
p = Path('toolmag-app/inventory/templates/inventory/dashboard.html')
if p.exists():
    text = read(p)
    text = re.sub(
        r'\n?<div class="actions">\s*<a class="button" href="\{% url \'checkout\' %\}">Nouvelle sortie</a>\s*<a class="button secondary" href="\{% url \'return_equipment\' %\}">Retour matériel</a>\s*</div>\s*',
        '\n<section class="panel access-note">\n  <h2>Flux matériel</h2>\n  <p class="hint">Les sorties et retours magasin ne sont pas lancés depuis le tableau de bord. Le point d’accès terrain reste le QR code, la fiche matériel, l’inventaire utilisateur ou l’appareil enregistré.</p>\n</section>\n',
        text,
        flags=re.S,
    )
    # Variante si le bloc a été formaté autrement
    text = text.replace('<div class="actions"><a class="button" href="{% url \'checkout\' %}">Nouvelle sortie</a><a class="button secondary" href="{% url \'return_equipment\' %}">Retour matériel</a></div>', '<section class="panel access-note"><h2>Flux matériel</h2><p class="hint">Les sorties et retours magasin ne sont pas lancés depuis le tableau de bord. Le point d’accès terrain reste le QR code, la fiche matériel, l’inventaire utilisateur ou l’appareil enregistré.</p></section>')
    write(p, text)

# Correctif cert_manager : Docker fallback lego doit utiliser /lego dans le conteneur, pas le chemin hôte.
p = Path('scripts/cert_manager.sh')
if p.exists():
    text = read(p)
    old = '''run_lego_cmd() {
  if has_lego; then
    DUCKDNS_TOKEN="$DUCKDNS_TOKEN" lego "$@"
    return $?
  fi
  if has_docker; then
    docker run --rm \\
      -e DUCKDNS_TOKEN="$DUCKDNS_TOKEN" \\
      -v "$SSL_DIR/lego:/lego" \\
      goacme/lego:latest \\
      "$@"
    return $?
  fi'''
    new = '''run_lego_cmd() {
  if has_lego; then
    DUCKDNS_TOKEN="$DUCKDNS_TOKEN" lego "$@"
    return $?
  fi
  if has_docker; then
    local args=("$@")
    local i
    for i in "${!args[@]}"; do
      if [[ "${args[$i]}" == "$SSL_DIR/lego" ]]; then
        args[$i]="/lego"
      fi
    done
    docker run --rm \\
      -e DUCKDNS_TOKEN="$DUCKDNS_TOKEN" \\
      -v "$SSL_DIR/lego:/lego" \\
      goacme/lego:latest \\
      "${args[@]}"
    return $?
  fi'''
    if old in text:
        text = text.replace(old, new)
    elif 'local args=("$@")' not in text and 'goacme/lego:latest' in text:
        text = text.replace('goacme/lego:latest \\\n      "$@"', 'goacme/lego:latest \\\n      "$@"')
    write(p, text)

# Script HTTPS DuckDNS minimal
write('scripts/configure_duckdns_https.sh', r'''#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

usage() {
  cat <<'EOF'
Usage:
  ./scripts/configure_duckdns_https.sh <domaine.duckdns.org> <email-letsencrypt> <duckdns-token> [port_https] [port_http]

Exemple standard public :
  ./scripts/configure_duckdns_https.sh stjo-lpsuite.duckdns.org nvivion.prof@gmail.com TOKEN_DUCKDNS 443 80

Exemple derrière box avec redirection externe 443 -> serveur:9443 :
  ./scripts/configure_duckdns_https.sh stjo-lpsuite.duckdns.org nvivion.prof@gmail.com TOKEN_DUCKDNS 9443 9000

Principe :
  - DNS-01 DuckDNS : pas besoin d'ouvrir le port 80 pour obtenir le certificat.
  - Nginx lp-gateway sert ensuite HTTPS sur GATEWAY_HTTPS_PORT.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 3 ]]; then
  usage
  exit 0
fi

DOMAIN="$1"
EMAIL="$2"
TOKEN="$3"
HTTPS_PORT="${4:-443}"
HTTP_PORT="${5:-80}"

DOMAIN="${DOMAIN#http://}"
DOMAIN="${DOMAIN#https://}"
DOMAIN="${DOMAIN%%/*}"
DOMAIN="${DOMAIN%%:*}"

if [[ "$DOMAIN" != *.duckdns.org ]]; then
  echo "ERREUR: ce script est prévu pour un domaine DuckDNS (*.duckdns.org). Domaine reçu: $DOMAIN" >&2
  exit 2
fi

if [[ ! -f .env ]]; then
  echo "ERREUR: .env introuvable. Lance d'abord l'installation." >&2
  exit 2
fi

cp .env ".env.backup-before-duckdns-https-$(date +%Y%m%d-%H%M%S)"

python3 - "$DOMAIN" "$EMAIL" "$TOKEN" "$HTTPS_PORT" "$HTTP_PORT" <<'PY'
from pathlib import Path
import sys

domain, email, token, https_port, http_port = sys.argv[1:6]
env = Path('.env')
lines = env.read_text(encoding='utf-8').splitlines()
values = {
    'LP_DEPLOY_MODE': 'public',
    'PUBLIC_DOMAIN': domain,
    'PUBLIC_SCHEME': 'https',
    'EXPOSURE_MODE': 'external',
    'EXTERNAL_PUBLIC_DOMAIN': domain,
    'ENABLE_HTTPS': '1',
    'GATEWAY_HTTP_PORT': http_port,
    'GATEWAY_HTTPS_PORT': https_port,
    'LP_CORE_PUBLIC_URL': f'https://{domain}',
    'TOOLMAG_PUBLIC_BASE_URL': f'https://{domain}/toolmag/',
    'TOOLMAG_PUBLIC_URL': f'https://{domain}/toolmag/',
    'SAFETY_PUBLIC_URL': f'https://{domain}/safety/',
    'PEDASHOP_PUBLIC_URL': f'https://{domain}/pedashop/',
    'CONSUMABLES_PUBLIC_URL': f'https://{domain}/pedashop/',
    'INVENTORY_PUBLIC_URL': f'https://{domain}/system/',
    'SYSTEM_MANAGER_PUBLIC_URL': f'https://{domain}/system/',
    'TPMANAGER_PUBLIC_URL': f'https://{domain}/tpmanager/',
    'PFMP_PUBLIC_URL': f'https://{domain}/pfmp/',
    'DJANGO_ALLOWED_HOSTS': f'localhost,127.0.0.1,{domain}',
    'CSRF_TRUSTED_ORIGINS': f'https://{domain},http://localhost:9000,http://127.0.0.1:9000',
    'SESSION_COOKIE_SECURE': '1',
    'CSRF_COOKIE_SECURE': '1',
    'SSL_DIR': './ssl',
    'SSL_CERT_FILE': '/ssl/fullchain.pem',
    'SSL_KEY_FILE': '/ssl/privkey.pem',
    'CERT_CHALLENGE_METHOD': 'dns_duckdns',
    'LETSENCRYPT_EMAIL': email,
    'DUCKDNS_TOKEN': token,
}

seen = set()
out = []
for line in lines:
    if not line or line.lstrip().startswith('#') or '=' not in line:
        out.append(line)
        continue
    key = line.split('=', 1)[0]
    if key in values:
        out.append(f'{key}={values[key]}')
        seen.add(key)
    else:
        out.append(line)
for key, value in values.items():
    if key not in seen:
        out.append(f'{key}={value}')
env.write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')

cert_env = Path('lp-core-db/data/cert-manager.env')
cert_env.parent.mkdir(parents=True, exist_ok=True)
cert_env.write_text('\n'.join(f'{k}={v}' for k, v in values.items() if k in {
    'PUBLIC_DOMAIN','PUBLIC_SCHEME','ENABLE_HTTPS','GATEWAY_HTTP_PORT','GATEWAY_HTTPS_PORT',
    'SSL_DIR','SSL_CERT_FILE','SSL_KEY_FILE','CERT_CHALLENGE_METHOD','LETSENCRYPT_EMAIL','DUCKDNS_TOKEN',
    'LP_CORE_PUBLIC_URL','TOOLMAG_PUBLIC_BASE_URL','SAFETY_PUBLIC_URL','PEDASHOP_PUBLIC_URL',
    'SYSTEM_MANAGER_PUBLIC_URL','TPMANAGER_PUBLIC_URL','PFMP_PUBLIC_URL','DJANGO_ALLOWED_HOSTS','CSRF_TRUSTED_ORIGINS'
}) + '\n', encoding='utf-8')
PY

chmod +x scripts/cert_manager.sh

echo "[1/4] Génération / installation du certificat Let's Encrypt DuckDNS"
./scripts/cert_manager.sh issue

echo "[2/4] Recréation rapide des conteneurs applicatifs pour recharger .env"
docker compose --env-file .env up -d --build lp-gateway lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app

echo "[3/4] Statut certificat"
./scripts/cert_manager.sh status

echo "[4/4] Contrôle HTTPS"
curl -k -sSI "https://${DOMAIN}:${HTTPS_PORT}/" | head || true

echo "HTTPS DuckDNS configuré. URL principale : https://${DOMAIN}${HTTPS_PORT:+:${HTTPS_PORT}}/"
echo "Si le port public externe est 443 redirigé vers ce port interne, l'URL utilisateur est simplement : https://${DOMAIN}/"
''')

# Script d'update rapide générique
write('update.sh', r'''#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

REPO="${LP_SUITE_REPO:-nvivionprof/lp-gestion-atelier-ep-suite}"
CHANNEL="stable"
ZIP=""
REPAIR_NO_CACHE=0
NO_BACKUP=0

usage() {
  cat <<'EOF'
Usage:
  ./update.sh [--channel stable|rc] [--zip /home/archive.zip] [--repair-no-cache] [--no-backup]

Update rapide par défaut :
  - sauvegarde complète obligatoire ;
  - remplacement du code uniquement ;
  - conservation .env, bases, médias, sauvegardes, SSL ;
  - docker compose up -d --build ;
  - migrations ;
  - contrôles simples.

Exemples :
  ./update.sh --channel stable
  ./update.sh --channel rc
  ./update.sh --zip /home/lp-suite.zip
  ./update.sh --channel rc --repair-no-cache
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --channel) CHANNEL="${2:?channel manquant}"; shift 2 ;;
    --zip) ZIP="${2:?zip manquant}"; shift 2 ;;
    --repair-no-cache) REPAIR_NO_CACHE=1; shift ;;
    --no-backup) NO_BACKUP=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Argument inconnu: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ ! -f .env ]]; then
  echo "ERREUR: .env introuvable. Ce script doit être lancé dans une installation existante." >&2
  exit 2
fi

mkdir -p /tmp/lp-suite-update
WORK="$(mktemp -d /tmp/lp-suite-update/update.XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

if [[ -z "$ZIP" ]]; then
  ZIP="$WORK/lp-suite-${CHANNEL}.zip"
  URL="https://github.com/${REPO}/archive/refs/heads/${CHANNEL}.zip"
  echo "Téléchargement $URL"
  curl -fL "$URL" -o "$ZIP"
fi

unzip -t "$ZIP" >/dev/null
unzip -q "$ZIP" -d "$WORK/src"
SRC="$(find "$WORK/src" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [[ -z "$SRC" || ! -d "$SRC" ]]; then
  echo "ERREUR: source extraite introuvable." >&2
  exit 2
fi

if [[ -f "$SRC/CHECKSUMS.sha256" ]]; then
  echo "Vérification CHECKSUMS de l'archive..."
  (cd "$SRC" && sha256sum -c CHECKSUMS.sha256 >/dev/null)
fi

if [[ "$NO_BACKUP" != "1" ]]; then
  if [[ -x ./scripts/full_backup.sh ]]; then
    echo "Sauvegarde avant update..."
    ./scripts/full_backup.sh "pre-update-$(date +%Y%m%d-%H%M%S)"
  else
    echo "ERREUR: scripts/full_backup.sh absent ou non exécutable. Utilise --no-backup uniquement en test." >&2
    exit 2
  fi
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "Installation rsync..."
  apt update && apt install -y rsync
fi

echo "Remplacement du code, conservation des données..."
rsync -a --delete \
  --exclude='.env' \
  --exclude='backups/' \
  --exclude='ssl/' \
  --exclude='imports/' \
  --exclude='postgres-db/' \
  --exclude='lp-core-db/' \
  --exclude='toolmag-db/' \
  --exclude='safety-db/' \
  --exclude='pedashop-db/' \
  --exclude='system-manager-db/' \
  --exclude='tpmanager-db/' \
  --exclude='pfmp-db/' \
  "$SRC"/ ./

chmod +x install.sh update.sh scripts/*.sh scripts/postgres/*.sh pfmp-app/docker-entrypoint.sh 2>/dev/null || true

if [[ -f CHECKSUMS.sha256 ]]; then
  echo "Vérification CHECKSUMS après rsync..."
  sha256sum -c CHECKSUMS.sha256 >/dev/null
fi

if [[ "$REPAIR_NO_CACHE" == "1" ]]; then
  echo "Mode réparation : rebuild no-cache. À utiliser seulement si images incohérentes."
  docker compose --env-file .env build --no-cache
  docker compose --env-file .env up -d
else
  echo "Update rapide : rebuild Docker incrémental."
  docker compose --env-file .env up -d --build
fi

if [[ -x ./scripts/migrate_all.sh ]]; then
  ./scripts/migrate_all.sh 2>&1 | tee /tmp/lp-suite-update-migrations.log
fi

docker compose --env-file .env ps

echo "Contrôle rapide routes/titres :"
for url in \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/toolmag/ \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/safety/ \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/pedashop/ \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/system/ \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/tpmanager/ \
  http://localhost:${GATEWAY_HTTP_PORT:-9000}/pfmp/
do
  echo
  echo "===== $url ====="
  curl -sSI "$url" | grep -Ei 'HTTP/|location:|x-lp-gateway-module' || true
  curl -sSL "$url" | grep -Eoi '<title>[^<]+' | head -n 1 || true
done

echo "Update terminé."
''')

# Documentation minimale
write('docs/HTTPS_DUCKDNS_RAPIDE.md', '''# HTTPS DuckDNS rapide — LP Gestion Atelier EP Suite

Objectif : activer HTTPS avec un domaine `*.duckdns.org` sans refaire une installation complète.

## Principe

- Challenge DNS-01 DuckDNS via lego.
- Pas besoin d'ouvrir le port 80 pour obtenir le certificat.
- Le portail Nginx `lp-gateway` sert ensuite HTTPS.
- Les bases, médias et sauvegardes ne sont pas modifiés.

## Commande

```bash
cd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-rc

./scripts/configure_duckdns_https.sh stjo-lpsuite.duckdns.org nvivion.prof@gmail.com TOKEN_DUCKDNS 443 80
```

Si la box redirige le port externe 443 vers le port interne 9443 du serveur :

```bash
./scripts/configure_duckdns_https.sh stjo-lpsuite.duckdns.org nvivion.prof@gmail.com TOKEN_DUCKDNS 9443 9000
```

## Variables modifiées

Le script met à jour `.env` :

```env
PUBLIC_DOMAIN=stjo-lpsuite.duckdns.org
PUBLIC_SCHEME=https
ENABLE_HTTPS=1
GATEWAY_HTTPS_PORT=443
LP_CORE_PUBLIC_URL=https://stjo-lpsuite.duckdns.org
TOOLMAG_PUBLIC_BASE_URL=https://stjo-lpsuite.duckdns.org/toolmag/
SESSION_COOKIE_SECURE=1
CSRF_COOKIE_SECURE=1
CERT_CHALLENGE_METHOD=dns_duckdns
```

## Renouvellement

```bash
./scripts/cert_manager.sh renew
```
''')

write('docs/UPDATE_RAPIDE_GIT.md', '''# Update rapide Git — LP Gestion Atelier EP Suite

## Commandes stables

Dernière version stable :

```bash
./update.sh --channel stable
```

Dernière RC :

```bash
./update.sh --channel rc
```

Archive locale :

```bash
./update.sh --zip /home/lp-suite.zip
```

## Règle

Un update ne fait pas de réinstallation complète :

- pas de `docker compose down -v` ;
- pas de `docker builder prune -af` ;
- pas de `--no-cache` par défaut ;
- conservation de `.env`, PostgreSQL, médias, sauvegardes, SSL et imports.

Le mode lourd est réservé à la réparation :

```bash
./update.sh --channel rc --repair-no-cache
```
''')

# Mise à jour README minimale
p = Path('README.md')
if p.exists():
    text = read(p)
    if '## Update rapide' not in text:
        text += '''

## Update rapide

```bash
./update.sh --channel stable
./update.sh --channel rc
```

Documentation : `docs/UPDATE_RAPIDE_GIT.md`.

## HTTPS DuckDNS

```bash
./scripts/configure_duckdns_https.sh stjo-lpsuite.duckdns.org email@example.com TOKEN_DUCKDNS 443 80
```

Documentation : `docs/HTTPS_DUCKDNS_RAPIDE.md`.
'''
    write(p, text)

# Permissions visibles dans Git
for path in ['update.sh', 'scripts/configure_duckdns_https.sh', 'scripts/cert_manager.sh']:
    if Path(path).exists():
        Path(path).chmod(0o755)
PYCODE

echo "[RC7] Nettoyage caches Python"
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

echo "[RC7] Vérification syntaxe des scripts"
bash -n update.sh
bash -n scripts/configure_duckdns_https.sh
bash -n scripts/cert_manager.sh

echo "[RC7] Recalcul CHECKSUMS.sha256"
cat > /tmp/rebuild_checksums_lp.py <<'PY'
from pathlib import Path
import hashlib
exclude_dirs = {'.git','backups','postgres-db','lp-core-db','toolmag-db','safety-db','pedashop-db','system-manager-db','tpmanager-db','pfmp-db','updates','logs','__pycache__'}
files = []
for path in Path('.').rglob('*'):
    if not path.is_file():
        continue
    if set(path.parts) & exclude_dirs:
        continue
    if path.name == 'CHECKSUMS.sha256' or path.suffix == '.pyc':
        continue
    files.append(path)
files = sorted(files, key=lambda p: str(p).replace('\\', '/'))
with open('CHECKSUMS.sha256', 'w', encoding='utf-8', newline='\n') as out:
    for path in files:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        clean = str(path).replace('\\', '/')
        out.write(f"{h.hexdigest()}  ./{clean}\n")
PY
python3 /tmp/rebuild_checksums_lp.py

sha256sum -c CHECKSUMS.sha256 2>&1 | grep -E 'FAILED|WARNING|No such file|did NOT match' || echo "CHECKSUMS OK"

echo "[RC7] Contrôles ciblés"
grep -R "Nouvelle sortie\|Retour matériel" -n toolmag-app/inventory/templates/inventory/dashboard.html && {
  echo "[ERREUR] Les boutons directs ToolMag sont encore présents." >&2
  exit 1
} || true

grep -R "configure_duckdns_https" -n scripts docs README.md >/dev/null && echo "HTTPS DuckDNS documenté"
grep -R -n -- "--repair-no-cache" update.sh docs/UPDATE_RAPIDE_GIT.md >/dev/null && echo "Update rapide documenté"

echo "[RC7] Patch appliqué. Commit conseillé :"
echo "git add -A && git commit -m 'Ajoute HTTPS DuckDNS, update rapide et accès ToolMag par inventaire'"
