#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
echo "[RC4] Correctifs propreté V0.0.1-RC4"

require_file(){
  [ -f "$1" ] || { echo "Fichier introuvable : $1" >&2; exit 1; }
}

for f in VERSION VERSION.txt scripts/load_demo_data.sh tpmanager-app/tp_manager/sync.py; do
  require_file "$f"
done

# 1) Version RC4.
printf 'V0.0.1-RC4\n' > VERSION
printf 'V0.0.1-RC4\n' > VERSION.txt
[ -f .suite-target-version ] && printf 'V0.0.1-RC4\n' > .suite-target-version

python3 - <<'PY'
from pathlib import Path
import json

p = Path('manifest.json')
if p.exists():
    data = json.loads(p.read_text(encoding='utf-8'))
    data['version'] = 'V0.0.1-RC4'
    data['suite_version'] = 'V0.0.1-RC4'
    data['release_stage'] = 'RC4'
    data['name'] = 'LP Gestion Atelier EP Suite — V0.0.1-RC4 exploitation encadrée'
    data['description'] = 'Release candidate technique de propreté : synchronisations post-installation sans erreur, API System Manager corrigée et dépendances requests stabilisées.'
    data.setdefault('changes', [])
    data['changes'].insert(0, 'RC4 : suppression des alertes post-installation résiduelles avant tag V0.0.1.')
    if 'github_wget' in data:
        data['github_wget']['release_asset'] = 'lp-gestion-atelier-ep-suite-V0.0.1-RC4.zip'
        data['github_wget']['checksum_asset'] = 'lp-gestion-atelier-ep-suite-V0.0.1-RC4.zip.sha256'
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY

# 2) Ne plus réimporter base_demo_lp_core.xlsx si seed_core a déjà créé les utilisateurs démo.
python3 - <<'PY'
from pathlib import Path
p = Path('scripts/load_demo_data.sh')
text = p.read_text(encoding='utf-8')
old = """if [ -f imports/base_demo_lp_core.xlsx ]; then
  log "LP Core : import imports/base_demo_lp_core.xlsx"
  run_manage lp-core-app import_users_xlsx /imports/base_demo_lp_core.xlsx || true
fi
"""
new = """if [ -f imports/base_demo_lp_core.xlsx ]; then
  CORE_DEMO_PRESENT="$(run_manage lp-core-app shell -c "from core.models import CoreUser; print(CoreUser.objects.filter(username='PROF-0001').exists())" 2>/dev/null | tail -n 1 || true)"
  if [ "$CORE_DEMO_PRESENT" = "True" ]; then
    log "LP Core : utilisateurs démo déjà présents, import XLSX ignoré pour éviter les doublons."
  else
    log "LP Core : import imports/base_demo_lp_core.xlsx"
    run_manage lp-core-app import_users_xlsx /imports/base_demo_lp_core.xlsx || true
  fi
fi
"""
if old not in text:
    raise SystemExit("Bloc import LP Core attendu non trouvé dans scripts/load_demo_data.sh")
p.write_text(text.replace(old, new), encoding='utf-8')
PY

# 3) Normaliser l'URL API System Manager côté TP Manager.
# En interne Docker, l'application System Manager est servie à la racine ; le préfixe public /system ne doit pas être appelé.
python3 - <<'PY'
from pathlib import Path
p = Path('tpmanager-app/tp_manager/sync.py')
text = p.read_text(encoding='utf-8')
if "def _normalize_internal_api_base" not in text:
    marker = """def _headers():
    return {'X-API-Key': settings.LP_CORE_API_TOKEN} if settings.LP_CORE_API_TOKEN else {}


"""
    helper = """def _headers():
    return {'X-API-Key': settings.LP_CORE_API_TOKEN} if settings.LP_CORE_API_TOKEN else {}


def _normalize_internal_api_base(raw_url: str, public_prefix: str = '') -> str:
    \"\"\"Retourne l'URL racine interne Docker d'une application.

    Les URL publiques utilisent parfois un préfixe de reverse proxy (/system,
    /tpmanager, etc.). Entre conteneurs Docker, Django reçoit l'application à
    la racine ; appeler /system/api/... provoque donc une 404.
    \"\"\"
    base = (raw_url or '').strip().rstrip('/')
    prefix = (public_prefix or '').strip().rstrip('/')
    if prefix and base.endswith(prefix):
        base = base[:-len(prefix)].rstrip('/')
    return base


"""
    if marker not in text:
        raise SystemExit("Point d'insertion _headers non trouvé dans tpmanager-app/tp_manager/sync.py")
    text = text.replace(marker, helper)

old = """def sync_systems_from_system_manager(timeout=30):
    url = settings.SYSTEM_MANAGER_API_URL.rstrip('/') + '/api/systems/'
"""
new = """def sync_systems_from_system_manager(timeout=30):
    base_url = _normalize_internal_api_base(settings.SYSTEM_MANAGER_API_URL, '/system')
    url = base_url + '/api/systems/'
"""
if old not in text:
    raise SystemExit("Bloc sync_systems_from_system_manager attendu non trouvé")
text = text.replace(old, new)
p.write_text(text, encoding='utf-8')
PY

# 4) Stabiliser les dépendances requests pour supprimer RequestsDependencyWarning.
# On ajoute des bornes explicites aux apps qui utilisent requests.
python3 - <<'PY'
from pathlib import Path

files = [
    Path('safety-app/requirements.txt'),
    Path('pedashop-app/requirements.txt'),
    Path('pfmp-app/requirements.txt'),
    Path('tpmanager-app/requirements.txt'),
    Path('system-manager-app/requirements.txt'),
]
pins = {
    'urllib3': 'urllib3==2.2.2',
    'charset-normalizer': 'charset-normalizer==3.3.2',
    'chardet': 'chardet==5.2.0',
}
for p in files:
    if not p.exists():
        continue
    lines = p.read_text(encoding='utf-8').splitlines()
    names = {line.split('==', 1)[0].split('>=', 1)[0].split('<=', 1)[0].strip().lower(): i for i, line in enumerate(lines) if line.strip() and not line.strip().startswith('#')}
    if 'requests' not in names:
        continue
    for name, pin in pins.items():
        if name in names:
            lines[names[name]] = pin
        else:
            lines.append(pin)
    p.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
PY

# 5) Mettre à jour le script de création des checksums, si présent, pour exclure caches Python et le checksum lui-même.
if [ -f scripts/create_checksums.sh ]; then
cat > scripts/create_checksums.sh <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

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
  -path '*/__pycache__/*' -prune -o \
  -type f ! -name 'CHECKSUMS.sha256' ! -name '*.pyc' -print0 \
  | sort -z \
  | xargs -0 sha256sum > CHECKSUMS.sha256
EOS
chmod +x scripts/create_checksums.sh
fi

# 6) Nettoyer caches Python et régénérer checksum.
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

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
  -path '*/__pycache__/*' -prune -o \
  -type f ! -name 'CHECKSUMS.sha256' ! -name '*.pyc' -print0 \
  | sort -z \
  | xargs -0 sha256sum > CHECKSUMS.sha256

echo "[RC4] Contrôles syntaxe"
bash -n scripts/load_demo_data.sh
python3 -m py_compile tpmanager-app/tp_manager/sync.py
sha256sum -c CHECKSUMS.sha256 2>&1 | grep -E 'FAILED|WARNING|No such file|did NOT match' && exit 1 || true

echo "[RC4] Correctifs appliqués. Attendu : git diff --stat, commit, push, tag V0.0.1-RC4."
