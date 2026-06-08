#!/usr/bin/env bash
set -euo pipefail

echo "[RC6-FIX] Application corrigée RC6 : menus, versions, héritages SQLite"

if [ ! -d .git ]; then
  echo "[ERREUR] Ce script doit être lancé dans le dépôt Git, pas dans le dossier d'installation extrait."
  echo "Chemin attendu : /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-git-rc2"
  exit 1
fi

python3 <<'PY'
from pathlib import Path
import json
import re

VERSION = "V0.0.1-RC6"
DISPLAY = "RC V0.0.1"

def read(path):
    return Path(path).read_text(encoding="utf-8")

def write(path, text):
    Path(path).write_text(text.rstrip() + "\n", encoding="utf-8")

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

if Path("scripts/version_manager.py").exists():
    text = read("scripts/version_manager.py")
    text = re.sub(r"V0\.0\.1-RC\d+", VERSION, text)
    text = text.replace("Bêta 2 V0.0.2", DISPLAY).replace("Bêta V0.0.2", DISPLAY)
    write("scripts/version_manager.py", text)

if Path(".env.example").exists():
    text = read(".env.example")
    text = re.sub(r'LP_CORE_VERSION=.*', f'LP_CORE_VERSION="LP Core — {DISPLAY}"', text)
    text = re.sub(r'APP_VERSION=.*', f'APP_VERSION="ToolMag — {DISPLAY}"', text)
    text = re.sub(r'SAFETY_VERSION=.*', f'SAFETY_VERSION="Safety Manager — {DISPLAY}"', text)
    text = re.sub(r'PEDASHOP_VERSION=.*', f'PEDASHOP_VERSION="PedaShop — {DISPLAY}"', text)
    text = re.sub(r'SYSTEM_MANAGER_VERSION=.*', f'SYSTEM_MANAGER_VERSION="System Manager — {DISPLAY}"', text)
    text = re.sub(r'TPMANAGER_VERSION=.*', f'TPMANAGER_VERSION="TP Manager — {DISPLAY}"', text)
    text = re.sub(r'PFMP_VERSION=.*', f'PFMP_VERSION="PFMP Manager — {DISPLAY}"', text)
    write(".env.example", text)

p = Path("lp-core-app/core/context_processors.py")
if p.exists():
    text = read(p)
    text = re.sub(r"SUITE_VERSION_LABEL\s*=\s*['\"][^'\"]+['\"]", f"SUITE_VERSION_LABEL = '{DISPLAY}'", text)
    write(p, text)

p = Path("lp-core-app/lp_core_project/settings.py")
if p.exists():
    text = read(p)
    text = re.sub(r"LP_CORE_VERSION\s*=\s*os\.getenv\('LP_CORE_VERSION',\s*'[^']+'\)", f"LP_CORE_VERSION = os.getenv('LP_CORE_VERSION', 'LP Core — {DISPLAY}')", text)
    write(p, text)

p = Path("lp-core-app/core/templates/core/base.html")
if p.exists():
    text = read(p)
    text = text.replace(
        '      {% for module in suite_modules %}<a href="{{ module.url }}">{{ module.name }}</a>{% endfor %}',
        '''      <details class="nav-dropdown"><summary>Applications</summary><div>
        <a href="{% url 'core_dashboard' %}">LP Core</a>
        {% for module in suite_modules %}<a href="{{ module.url }}">{{ module.name }}</a>{% endfor %}
      </div></details>'''
    )
    text = text.replace('          <a href="{% url \'core_suite_updates\' %}">Mises à jour</a>\n', '')
    text = text.replace('          <a href="{% url \'sql_database_admin\' %}">Base SQL</a>\n', '')
    write(p, text)

p = Path("lp-core-app/lp_core_project/urls.py")
if p.exists():
    lines = []
    for line in read(p).splitlines():
        if "base-sql/" in line or "sql_database_" in line:
            continue
        lines.append(line)
    write(p, "\n".join(lines))

p = Path("toolmag-app/inventory/context_processors.py")
if p.exists():
    text = read(p)
    if "def _person_label(" not in text:
        text = text.replace(
            "def _person_from_session(code, *, require_storekeeper=False):",
            """def _person_label(person):
    if not person:
        return ''
    first = (getattr(person, 'first_name', '') or '').strip()
    last = (getattr(person, 'last_name', '') or '').strip()
    full = f"{first} {last}".strip()
    return full or getattr(person, 'name', '') or getattr(person, 'username', '') or getattr(person, 'code', '')


def _person_from_session(code, *, require_storekeeper=False):"""
        )
    old = """    return {
        'tm_current_storekeeper': storekeeper,
        'tm_current_borrower': borrower,
        'tm_is_prof': is_prof,
        'TOOLMAG_VERSION_LABEL': version,
        'TOOLMAG_VERSION_DETAIL': version,
        'TOOLMAG_LANG': (request.session.get('toolmag_lang') or translation.get_language() or 'fr')[:2],
        'LP_CORE_PUBLIC_URL': getattr(settings, 'LP_CORE_PUBLIC_URL', ''),
    }"""
    new = """    lp_core_url = getattr(settings, 'LP_CORE_PUBLIC_URL', '').rstrip('/')
    return {
        'tm_current_storekeeper': storekeeper,
        'tm_current_borrower': borrower,
        'tm_current_storekeeper_label': _person_label(storekeeper),
        'tm_current_borrower_label': _person_label(borrower),
        'tm_is_prof': is_prof,
        'TOOLMAG_VERSION_LABEL': version,
        'TOOLMAG_VERSION_DETAIL': version,
        'TOOLMAG_LANG': (request.session.get('toolmag_lang') or translation.get_language() or 'fr')[:2],
        'LP_CORE_PUBLIC_URL': lp_core_url,
        'SUITE_APP_LINKS': [
            {'name': 'LP Core', 'url': lp_core_url or '/'},
            {'name': 'ToolMag', 'url': getattr(settings, 'TOOLMAG_PUBLIC_BASE_URL', '/toolmag/').rstrip('/') + '/'},
            {'name': 'Safety Manager', 'url': getattr(settings, 'SAFETY_PUBLIC_URL', '/safety/').rstrip('/') + '/'},
            {'name': 'PedaShop', 'url': getattr(settings, 'PEDASHOP_PUBLIC_URL', '/pedashop/').rstrip('/') + '/'},
            {'name': 'System Manager', 'url': getattr(settings, 'SYSTEM_MANAGER_PUBLIC_URL', '/system/').rstrip('/') + '/'},
            {'name': 'TP Manager', 'url': getattr(settings, 'TPMANAGER_PUBLIC_URL', '/tpmanager/').rstrip('/') + '/'},
            {'name': 'PFMP Manager', 'url': getattr(settings, 'PFMP_PUBLIC_URL', '/pfmp/').rstrip('/') + '/'},
        ],
    }"""
    if old in text:
        text = text.replace(old, new)
    write(p, text)

p = Path("toolmag-app/inventory/templates/inventory/base.html")
if p.exists():
    text = read(p)
    insertion = """    <details class="admin-dropdown">
      <summary>Applications</summary>
      <div class="admin-dropdown-menu" aria-label="Applications LP Gestion Atelier">
        {% for app in SUITE_APP_LINKS %}
          <a class="admin-menu-item" href="{{ app.url }}">{{ app.name }}</a>
        {% endfor %}
      </div>
    </details>
"""
    if 'aria-label="Applications LP Gestion Atelier"' not in text:
        text = text.replace('    <a href="{% url \'display_current_loans\' %}">Affichage dynamique</a>\n', '    <a href="{% url \'display_current_loans\' %}">Affichage dynamique</a>\n' + insertion)
    text = text.replace('          <a class="admin-menu-item" title="Retour LP Core" href="{{ LP_CORE_PUBLIC_URL }}" target="_blank" rel="noopener">LP Core élèves</a>\n', '')
    text = text.replace('          <a class="admin-menu-item" title="Sauvegardes" href="{% url \'backups_management\' %}">Sauvegardes</a>\n', '')
    text = text.replace('          <a class="admin-menu-item" title="Base SQL" href="{% url \'sql_database_admin\' %}">Base SQL</a>\n', '')
    text = text.replace('{{ request.session.borrower_code }}', '{{ tm_current_borrower_label|default:request.session.borrower_code }}')
    text = text.replace('{{ request.session.storekeeper_code }}', '{{ tm_current_storekeeper_label|default:request.session.storekeeper_code }}')
    write(p, text)

p = Path("toolmag-app/inventory/urls.py")
if p.exists():
    lines = read(p).splitlines()
    existing_login = any("path('login/'" in l for l in lines)
    out = []
    for line in lines:
        if "path('role/'" in line and not existing_login:
            out.append(line)
            out.append("    path('login/', views.role_choice, name='legacy_login'),")
            continue
        if "admin-toolmag/sauvegardes/" in line or "admin-toolmag/base-sql" in line or "sql_database_" in line or "backups_management" in line:
            continue
        out.append(line)
    write(p, "\n".join(out))

for p in Path('.').glob('*/Dockerfile'):
    text = read(p)
    if 'PIP_ROOT_USER_ACTION=ignore' not in text:
        lines = text.splitlines()
        out = []
        inserted = False
        for line in lines:
            out.append(line)
            if not inserted and line.strip().startswith('FROM '):
                out.append('ENV PIP_ROOT_USER_ACTION=ignore')
                inserted = True
        write(p, "\n".join(out))
PY

echo "[RC6-FIX] Nettoyage caches Python"
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

echo "[RC6-FIX] Recalcul CHECKSUMS.sha256"
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
        out.write(f"{h.hexdigest()}  ./{str(path).replace('\\', '/')}\n")
PY
python3 /tmp/rebuild_checksums_lp.py
sha256sum -c CHECKSUMS.sha256 2>&1 | grep -E 'FAILED|WARNING|No such file|did NOT match' && { echo "[ERREUR] CHECKSUMS incorrect"; exit 1; } || echo "CHECKSUMS OK"

echo "[RC6-FIX] Terminé. Vérifie git diff --stat puis commit/push/tag."
