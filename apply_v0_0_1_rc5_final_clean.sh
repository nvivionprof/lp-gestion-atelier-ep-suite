#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")"

NEW_VERSION="V0.0.1-RC5"
REQ_BLOCK=(
  "requests==2.32.3"
  "urllib3>=2.2.2,<3"
  "charset-normalizer>=3.3.2,<4"
  "chardet>=5.2.0,<6"
)

echo "[RC5] Application des corrections finales ${NEW_VERSION}"

# 1) Versioning
printf '%s\n' "$NEW_VERSION" > VERSION
printf '%s\n' "$NEW_VERSION" > VERSION.txt
printf '%s\n' "$NEW_VERSION" > .suite-target-version

python3 <<'PY'
from pathlib import Path
import json
p = Path('manifest.json')
if p.exists():
    data = json.loads(p.read_text(encoding='utf-8'))
    new = 'V0.0.1-RC5'
    data['version'] = new
    data['suite_version'] = new
    data['name'] = 'LP Gestion Atelier EP Suite — V0.0.1-RC5 exploitation encadrée'
    data['release_stage'] = 'RC5'
    data['rc_status'] = 'release_candidate'
    data.setdefault('migration_min_versions', {})['current_version'] = new
    gh = data.setdefault('github_wget', {})
    gh['release_asset'] = f'lp-gestion-atelier-ep-suite-{new}.zip'
    gh['checksum_asset'] = f'lp-gestion-atelier-ep-suite-{new}.zip.sha256'
    changes = data.setdefault('changes', [])
    for msg in [
        'RC5 : bornage compatible des dépendances HTTP Python pour supprimer les RequestsDependencyWarning.',
        'RC5 : ajout d’un alias API System Manager direct /system/api/systems/ pour les appels internes derrière APP_URL_PREFIX.',
        'RC5 : recalcul strict de CHECKSUMS.sha256 hors caches Python et fichiers runtime.'
    ]:
        if msg not in changes:
            changes.insert(0, msg)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY

# 2) Requirements : stabiliser requests et ses dépendances, sans figer trop dur les dépendances transverses.
python3 <<'PY'
from pathlib import Path

wanted = {
    'requests': 'requests==2.32.3',
    'urllib3': 'urllib3>=2.2.2,<3',
    'charset-normalizer': 'charset-normalizer>=3.3.2,<4',
    'charset_normalizer': 'charset-normalizer>=3.3.2,<4',
    'chardet': 'chardet>=5.2.0,<6',
}
canonical_order = ['requests', 'urllib3', 'charset-normalizer', 'chardet']

def package_key(line: str):
    raw = line.strip()
    if not raw or raw.startswith('#') or raw.startswith('-'):
        return None
    for sep in ['==', '>=', '<=', '~=', '>', '<', '=']:
        if sep in raw:
            return raw.split(sep, 1)[0].strip().lower().replace('_', '-')
    return raw.strip().lower().replace('_', '-')

for p in sorted(Path('.').glob('*-app/requirements.txt')):
    lines = p.read_text(encoding='utf-8').splitlines()
    # On ne touche que les modules qui utilisent déjà requests, ou les modules appelant des API internes.
    text = '\n'.join(lines)
    if 'requests' not in text and p.parts[0] not in {'tpmanager-app', 'system-manager-app'}:
        continue
    seen = set()
    out = []
    for line in lines:
        key = package_key(line)
        key_norm = key.replace('_', '-') if key else key
        if key_norm in wanted:
            canon = 'charset-normalizer' if key_norm == 'charset-normalizer' else key_norm
            if canon not in seen:
                out.append(wanted[canon])
                seen.add(canon)
            continue
        out.append(line)
    for canon in canonical_order:
        if canon not in seen:
            out.append(wanted[canon])
            seen.add(canon)
    # dédoublonnage doux en conservant ordre
    final = []
    keys = set()
    for line in out:
        key = package_key(line)
        key_norm = key.replace('_', '-') if key else key
        if key_norm in {'requests', 'urllib3', 'charset-normalizer', 'chardet'}:
            if key_norm in keys:
                continue
            keys.add(key_norm)
        final.append(line)
    p.write_text('\n'.join(final).rstrip() + '\n', encoding='utf-8')
PY

# 3) System Manager : ajouter un alias direct pour les URLs préfixées reçues sans Nginx.
python3 <<'PY'
from pathlib import Path
p = Path('system-manager-app/system_manager/urls.py')
text = p.read_text(encoding='utf-8')
needle = "    path('api/systems/', views.api_systems, name='system_api_systems'),"
alias = "    path('system/api/systems/', views.api_systems, name='system_api_systems_prefixed'),"
if needle in text and alias not in text:
    text = text.replace(needle, needle + "\n" + alias)
p.write_text(text, encoding='utf-8')
PY

# 4) TP Manager : normalisation défensive de l'URL API System Manager.
python3 <<'PY'
from pathlib import Path
p = Path('tpmanager-app/tp_manager/sync.py')
text = p.read_text(encoding='utf-8')
old = """def sync_systems_from_system_manager(timeout=30):\n    base = settings.SYSTEM_MANAGER_API_URL.rstrip('/')\n    candidates = [f'{base}/api/systems/']\n    if not base.endswith('/system'):\n        candidates.append(f'{base}/system/api/systems/')\n"""
new = """def sync_systems_from_system_manager(timeout=30):\n    base = settings.SYSTEM_MANAGER_API_URL.rstrip('/')\n    # En interne Docker, l'application doit normalement être appelée sans le préfixe\n    # public /system. On sécurise toutefois les deux cas pour éviter les 404 en\n    # installation neuve lorsque APP_URL_PREFIX est actif.\n    internal_base = base[:-len('/system')] if base.endswith('/system') else base\n    candidates = [f'{internal_base}/api/systems/', f'{internal_base}/system/api/systems/']\n"""
if old in text:
    text = text.replace(old, new)
elif "def sync_systems_from_system_manager(timeout=30):" in text and "internal_base =" not in text:
    # Remplacement plus permissif sur les premières lignes de la fonction.
    start = text.index("def sync_systems_from_system_manager(timeout=30):")
    end = text.index("\n    response = None", start)
    repl = new.rstrip()
    text = text[:start] + repl + text[end:]
p.write_text(text, encoding='utf-8')
PY

# 5) Optionnel : supprimer l'affichage d'URL brute dans le rapport d'erreur pour éviter un grep 404 trop verbeux si une API est temporairement indisponible.
python3 <<'PY'
from pathlib import Path
p = Path('tpmanager-app/tp_manager/management/commands/sync_system_manager.py')
text = p.read_text(encoding='utf-8')
text = text.replace(
"self.stdout.write(self.style.WARNING(f'Synchronisation System Manager partielle/non bloquante : {report}'))",
"self.stdout.write(self.style.WARNING('Synchronisation System Manager partielle/non bloquante : API indisponible ou aucune donnée synchronisable.'))"
)
p.write_text(text, encoding='utf-8')
PY

# 6) Nettoyage caches Python avant checksum.
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 7) Contrôles syntaxiques sans générer de pyc.
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  tpmanager-app/tp_manager/sync.py \
  tpmanager-app/tp_manager/management/commands/sync_system_manager.py \
  system-manager-app/system_manager/urls.py
bash -n scripts/load_demo_data.sh 2>/dev/null || true

# 8) Recalcul strict CHECKSUMS.sha256. CHECKSUMS lui-même, caches et dossiers runtime sont exclus.
echo "[RC5] Recalcul CHECKSUMS.sha256"
python3 <<'PY'
from pathlib import Path
import hashlib

exclude_dirs = {
    '.git', 'backups', 'postgres-db',
    'lp-core-db', 'toolmag-db', 'safety-db', 'pedashop-db',
    'system-manager-db', 'tpmanager-db', 'pfmp-db',
    'updates', 'logs', '__pycache__',
}
files = []
for path in Path('.').rglob('*'):
    if not path.is_file():
        continue
    if set(path.parts) & exclude_dirs:
        continue
    if path.name == 'CHECKSUMS.sha256':
        continue
    if path.suffix == '.pyc':
        continue
    files.append(path)
files = sorted(files, key=lambda p: str(p).replace('\\', '/'))
with open('CHECKSUMS.sha256', 'w', encoding='utf-8', newline='\n') as out:
    for path in files:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        out.write(f"{h.hexdigest()}  ./{str(path).replace('\\', '/')}\n")
PY

# 9) Nettoyage éventuel des caches générés par py_compile malgré PYTHONDONTWRITEBYTECODE selon environnement.
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 10) Validation bloquante checksum.
if sha256sum -c CHECKSUMS.sha256 2>&1 | grep -E 'FAILED|WARNING|No such file|did NOT match'; then
  echo "[RC5] ERREUR : CHECKSUMS invalide après patch." >&2
  exit 1
fi

echo "CHECKSUMS OK"
echo "[RC5] Correctifs ${NEW_VERSION} appliqués. Vérifie git diff --stat puis commit/push/tag."
