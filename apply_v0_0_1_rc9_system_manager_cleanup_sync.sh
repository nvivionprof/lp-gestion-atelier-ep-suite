#!/usr/bin/env bash
set -euo pipefail

echo "[RC9] System Manager : suppression ancien SQL admin + synchronisation LP Core corrigée"

python3 <<'PY'
from pathlib import Path
import hashlib
import json
import re

ROOT = Path.cwd()
VERSION = "V0.0.1-RC9"

# ---------- Version ----------
for rel in ["VERSION", "VERSION.txt", ".suite-target-version"]:
    p = ROOT / rel
    if p.exists():
        p.write_text(VERSION + "\n", encoding="utf-8")

manifest = ROOT / "manifest.json"
if manifest.exists():
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    for key in ["version", "suite_version", "target_version"]:
        if key in data:
            data[key] = VERSION
    if "version" not in data:
        data["version"] = VERSION
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---------- System Manager : suppression routes admin-sql ----------
urls = ROOT / "system-manager-app/system_manager/urls.py"
if urls.exists():
    text = urls.read_text(encoding="utf-8")
    remove_patterns = [
        "path('admin-sql/', views.sql_database_admin, name='sql_database_admin'),",
        "path('admin-sql/export.sql', views.sql_database_export, name='sql_database_export'),",
        "path('admin-sql/import/', views.sql_database_import, name='sql_database_import'),",
    ]
    for pat in remove_patterns:
        text = text.replace("    " + pat + "\n", "")
        text = text.replace(pat + "\n", "")
    urls.write_text(text, encoding="utf-8")

# ---------- System Manager : menu admin sans sync direct et sans Base SQL ----------
base = ROOT / "system-manager-app/system_manager/templates/system_manager/base.html"
if base.exists():
    text = base.read_text(encoding="utf-8")
    lines = []
    for line in text.splitlines():
        if "system_sync_lp_core" in line:
            continue
        if "sql_database_admin" in line or "Base SQL" in line:
            continue
        lines.append(line)
    base.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

# ---------- System Manager : suppression template ancienne base SQL ----------
sql_template = ROOT / "system-manager-app/system_manager/templates/system_manager/sql_database.html"
if sql_template.exists():
    sql_template.unlink()

# ---------- System Manager : suppression des vues SQL admin obsolètes ----------
views = ROOT / "system-manager-app/system_manager/views.py"
if views.exists():
    text = views.read_text(encoding="utf-8")
    text = re.sub(
        r"\n# --- Administration SQL base module ---\n"
        r"def sql_database_admin\(request\):.*?"
        r"def help_view\(request\):",
        "\n# --- Administration SQL base module supprimée : sauvegarde/restauration centralisée dans LP Core ---\n"
        "def help_view(request):",
        text,
        flags=re.S,
    )
    views.write_text(text, encoding="utf-8")

# ---------- System Manager : explication dans Paramétrage ----------
ref = ROOT / "system-manager-app/system_manager/templates/system_manager/referentials.html"
if ref.exists():
    text = ref.read_text(encoding="utf-8")
    if "Synchronisation LP Core → System Manager" not in text:
        text = text.replace(
            "<section class=\"hero\"><div><p class=\"eyebrow\">Administration</p><h1>Paramétrage System Manager</h1>",
            "<section class=\"hero\"><div><p class=\"eyebrow\">Administration</p><h1>Paramétrage System Manager</h1>",
        )
    # Ajout d'un bloc lisible juste après la section hero si absent.
    if "system-sync-explain" not in text:
        insertion = """
<section class=\"panel system-sync-explain\">
  <h2>Synchronisations des référentiels</h2>
  <p class=\"muted\"><strong>LP Core → System Manager</strong> récupère les formations, classes, zones, sous-zones et blocs atelier validés dans LP Core. C'est le sens normal de référence.</p>
  <p class=\"muted\"><strong>System Manager → LP Core</strong> renvoie vers LP Core les zones, sous-zones et blocs créés localement dans System Manager. Cette action nécessite le jeton interne LP Core et n'est accessible que depuis cette page de paramétrage.</p>
</section>
"""
        text = text.replace("</section>\n<div class=\"grid2\">", "</section>\n" + insertion + "\n<div class=\"grid2\">", 1)
    ref.write_text(text, encoding="utf-8")

# ---------- LP Core : corriger 403 CSRF sur API interne System Manager -> LP Core ----------
core_views = ROOT / "lp-core-app/core/views.py"
if core_views.exists():
    text = core_views.read_text(encoding="utf-8")
    if "from django.views.decorators.csrf import csrf_exempt" not in text:
        text = text.replace(
            "from django.views.decorators.http import require_http_methods\n",
            "from django.views.decorators.http import require_http_methods\nfrom django.views.decorators.csrf import csrf_exempt\n",
        )
    # Ajouter csrf_exempt uniquement sur l'endpoint API interne concerné.
    text = text.replace(
        "@require_http_methods(['POST'])\ndef api_system_manager_referentials_import(request):",
        "@csrf_exempt\n@require_http_methods(['POST'])\ndef api_system_manager_referentials_import(request):",
    )
    # éviter double décorateur si script relancé
    text = text.replace("@csrf_exempt\n@csrf_exempt\n@require_http_methods(['POST'])\ndef api_system_manager_referentials_import", "@csrf_exempt\n@require_http_methods(['POST'])\ndef api_system_manager_referentials_import")
    core_views.write_text(text, encoding="utf-8")

# ---------- Documentation RC9 ----------
doc = ROOT / "docs/RC9_SYSTEM_MANAGER_CLEANUP_SYNC.md"
doc.parent.mkdir(parents=True, exist_ok=True)
doc.write_text("""# RC9 — System Manager : nettoyage SQL et synchronisation LP Core

## Corrections

- Suppression de l'ancienne page SQLite `/system/admin-sql/`.
- Suppression de l'entrée `Base SQL` dans le menu System Manager.
- Suppression de la synchronisation directe depuis le menu admin System Manager.
- Conservation des synchronisations uniquement dans `Paramétrage`.
- Correction du 403 lors de `System Manager → LP Core` : l'endpoint LP Core `/api/system-manager/referentials/import/` est une API interne authentifiée par `X-API-Key`; elle ne doit pas être bloquée par le CSRF navigateur.

## Contrôles attendus

```bash
curl -sSI http://localhost:9000/system/admin-sql/ | head
```

La page ne doit plus être active.

```bash
curl -sSL http://localhost:9000/system/ | grep -Ei 'Base SQL|Synchroniser LP Core' || echo OK
```

Le menu admin ne doit plus afficher ces entrées.
""", encoding="utf-8")

# ---------- README minimal ----------
readme = ROOT / "README.md"
if readme.exists() and "RC9 — System Manager" not in readme.read_text(encoding="utf-8", errors="ignore"):
    with readme.open("a", encoding="utf-8") as f:
        f.write("\n\n## RC9 — System Manager\n\n- Suppression de l'ancien admin SQL `/system/admin-sql/`.\n- Synchronisation System Manager → LP Core corrigée côté CSRF/API interne.\n- Synchronisations visibles uniquement depuis Paramétrage.\n")

# ---------- Nettoyage caches ----------
for p in ROOT.rglob("__pycache__"):
    if p.is_dir():
        import shutil
        shutil.rmtree(p)
for p in ROOT.rglob("*.pyc"):
    p.unlink()

# ---------- Checksums ----------
exclude_dirs = {
    '.git', 'backups', 'postgres-db', 'lp-core-db', 'toolmag-db', 'safety-db', 'pedashop-db',
    'system-manager-db', 'tpmanager-db', 'pfmp-db', 'updates', 'logs', '__pycache__'
}
files = []
for path in ROOT.rglob('*'):
    if not path.is_file():
        continue
    rel_parts = set(path.relative_to(ROOT).parts)
    if rel_parts & exclude_dirs:
        continue
    if path.name == 'CHECKSUMS.sha256' or path.suffix == '.pyc':
        continue
    files.append(path)
files.sort(key=lambda p: str(p.relative_to(ROOT)).replace('\\', '/'))
with (ROOT / 'CHECKSUMS.sha256').open('w', encoding='utf-8', newline='\n') as out:
    for path in files:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        rel = str(path.relative_to(ROOT)).replace('\\', '/')
        out.write(f"{h.hexdigest()}  ./{rel}\n")

print("RC9 patch appliqué.")
PY

echo "[RC9] Vérification syntaxe Python/Django basique"
python3 -m py_compile lp-core-app/core/views.py system-manager-app/system_manager/views.py

echo "[RC9] Vérification syntaxe Bash"
bash -n update.sh 2>/dev/null || true
bash -n upgrade.sh 2>/dev/null || true

echo "[RC9] Vérification CHECKSUMS"
sha256sum -c CHECKSUMS.sha256 2>&1 | grep -E 'FAILED|WARNING|No such file|did NOT match' && exit 1 || echo "CHECKSUMS OK"

echo "[RC9] Contrôles ciblés"
grep -R "admin-sql" -n system-manager-app/system_manager/urls.py system-manager-app/system_manager/templates/system_manager/base.html && { echo "Ancienne route/menu admin-sql encore présent"; exit 1; } || echo "Ancien admin-sql System Manager retiré des routes/menu"
grep -R "system_sync_lp_core\|Synchroniser LP Core" -n system-manager-app/system_manager/templates/system_manager/base.html && { echo "Sync encore visible dans le menu admin"; exit 1; } || echo "Sync retirée du menu admin"
grep -n "csrf_exempt" lp-core-app/core/views.py | grep -q . && echo "csrf_exempt présent côté LP Core"

echo "[RC9] Patch appliqué. Commit conseillé :"
echo "git add -A && git commit -m 'RC9 nettoie System Manager SQL et corrige sync LP Core'"
