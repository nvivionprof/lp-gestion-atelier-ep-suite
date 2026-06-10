#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
VERSION="V0.0.1-RC12"

if [[ ! -f "docker-compose.yml" ]]; then
  echo "Erreur : lance ce script depuis la racine du dépôt LP Gestion Atelier EP Suite."
  exit 1
fi

python3 - <<'PY'
from pathlib import Path
import re
from datetime import datetime

root = Path.cwd()
version = "V0.0.1-RC12"

def read(p):
    path = root / p
    return path.read_text(encoding='utf-8') if path.exists() else None

def write(p, text):
    path = root / p
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

def replace_once(text, old, new):
    if old in text:
        return text.replace(old, new, 1)
    return text

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
for p in ["VERSION", "VERSION.txt", ".suite-target-version"]:
    if (root / p).exists():
        write(p, version + "\n")

manifest = root / "manifest.json"
if manifest.exists():
    txt = manifest.read_text(encoding='utf-8')
    txt = re.sub(r'"version"\s*:\s*"[^"]+"', f'"version": "{version}"', txt)
    manifest.write_text(txt, encoding='utf-8')

# ---------------------------------------------------------------------------
# LP Core : rights TextField + migration
# ---------------------------------------------------------------------------
models_path = "lp-core-app/core/models.py"
txt = read(models_path)
if txt:
    txt = txt.replace("rights = models.CharField(max_length=255, blank=True, help_text='Droits séparés par ;')",
                      "rights = models.TextField(blank=True, help_text='Droits séparés par ;')")
    write(models_path, txt)

mig_dir = root / "lp-core-app/core/migrations"
if mig_dir.exists():
    target = mig_dir / "9991_rc12_coreuser_rights_textfield.py"
    if not target.exists():
        existing = sorted([p for p in mig_dir.glob("*.py") if p.name != "__init__.py" and p.name != target.name])
        dep_name = existing[-1].stem if existing else "0001_initial"
        target.write_text(f"""from django.db import migrations, models\n\n\nclass Migration(migrations.Migration):\n\n    dependencies = [\n        ('core', '{dep_name}'),\n    ]\n\n    operations = [\n        migrations.AlterField(\n            model_name='coreuser',\n            name='rights',\n            field=models.TextField(blank=True, help_text='Droits séparés par ;'),\n        ),\n    ]\n""", encoding='utf-8')

# ---------------------------------------------------------------------------
# LP Core : gestion par lot - rôle principal + droits PFMP + pleine largeur
# ---------------------------------------------------------------------------
views_path = "lp-core-app/core/views.py"
txt = read(views_path)
if txt:
    # normalisation droits : pas de droits vides, suppression doublons
    txt = txt.replace("rights.update(selected_rights)", "rights.update([r for r in selected_rights if r])")
    txt = txt.replace("rights.difference_update(selected_rights)", "rights.difference_update([r for r in selected_rights if r])")
    txt = txt.replace("u.rights = ';'.join(sorted(rights))", "u.rights = ';'.join(sorted(r for r in rights if r))")
    if "elif action == 'set_role':" not in txt and "elif action in {'add_store', 'remove_store'}:" in txt:
        block = """elif action == 'set_role':\n            target_role = request.POST.get('target_role') or ''\n            valid_roles = {code for code, _label in CoreUser.ROLE_CHOICES}\n            if target_role in valid_roles:\n                count = 0\n                for u in target_qs:\n                    u.role_principal = target_role\n                    u.save(update_fields=['role_principal', 'updated_at'])\n                    count += 1\n                messages.success(request, f'Rôle principal mis à jour sur {count} utilisateur(s).')\n                log_core_action(actor, 'SET_ROLE', 'bulk', target_role)\n            else:\n                messages.error(request, 'Rôle principal invalide.')\n        """
        txt = txt.replace("elif action in {'add_store', 'remove_store'}:", block + "elif action in {'add_store', 'remove_store'}:", 1)
    write(views_path, txt)

tpl_path = "lp-core-app/core/templates/core/bulk_permissions.html"
txt = read(tpl_path)
if txt:
    if "bulk-rc12-full-width" not in txt:
        txt = txt.replace("{% block content %}", "{% block content %}\n<style>\n  .container{max-width:100%!important;width:100%!important;margin:0!important;padding:18px 24px!important;}\n  .bulk-rc12-full-width{width:100%;}\n  .bulk-rc12-full-width .rights-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:.55rem;}\n  .bulk-rc12-full-width .rights-grid label{min-height:48px;}\n</style>\n<div class=\"bulk-rc12-full-width\">", 1)
        txt = txt.replace("{% endblock %}", "</div>\n{% endblock %}")
    if '<option value="set_role">Modifier rôle principal</option>' not in txt:
        txt = txt.replace("<option value=\"remove_right\">Retirer droit</option>", "<option value=\"remove_right\">Retirer droit</option><option value=\"set_role\">Modifier rôle principal</option>", 1)
    if 'data-actions="set_role"' not in txt:
        role_block = """

    <div class="bulk-block" data-actions="set_role">
      <h3>Rôle principal</h3>
      <p class="muted">Le rôle principal structure l’usage général du compte. Les droits restent indépendants et complètent ce rôle.</p>
      <label>Nouveau rôle principal
        <select name="target_role">
          {% for code,label in roles %}<option value="{{ code }}">{{ label }}</option>{% endfor %}
        </select>
      </label>
    </div>
"""
        txt = txt.replace("\n    <div class=\"bulk-block\" data-actions=\"add_store remove_store\">", role_block + "\n    <div class=\"bulk-block\" data-actions=\"add_store remove_store\">", 1)
    if 'MODULE_PFMP' not in txt:
        pfmp_rights = """
        <label data-filter="MODULE_PFMP core pfmp portail stage"><input type="checkbox" name="rights_codes" value="MODULE_PFMP"> <span>MODULE_PFMP</span><small>core — Voir PFMP Manager dans le portail</small></label>
        <label data-filter="PFMP_ADMIN pfmp administration"><input type="checkbox" name="rights_codes" value="PFMP_ADMIN"> <span>PFMP_ADMIN</span><small>pfmp — Administration PFMP Manager</small></label>
        <label data-filter="PFMP_PROF pfmp professeur suivi élèves"><input type="checkbox" name="rights_codes" value="PFMP_PROF"> <span>PFMP_PROF</span><small>pfmp — Suivi PFMP professeur</small></label>
        <label data-filter="PFMP_ELEVE pfmp élève portail"><input type="checkbox" name="rights_codes" value="PFMP_ELEVE"> <span>PFMP_ELEVE</span><small>pfmp — Accès élève PFMP</small></label>
        <label data-filter="PFMP_EXPORT_ACTIVITE pfmp export pdf"><input type="checkbox" name="rights_codes" value="PFMP_EXPORT_ACTIVITE"> <span>PFMP_EXPORT_ACTIVITE</span><small>pfmp — Export PDF activité PFMP</small></label>
"""
        txt = txt.replace("{% empty %}<p>Aucun droit paramétré.</p>{% endfor %}", "{% empty %}<p>Aucun droit paramétré.</p>{% endfor %}" + pfmp_rights, 1)
    write(tpl_path, txt)

# ---------------------------------------------------------------------------
# CSS pastilles style ToolMag sur tous les modules
# ---------------------------------------------------------------------------
role_css = r'''

/* RC12 — pastilles de connexion harmonisées type ToolMag */
.topbar .lp-role-pill,
.topbar .role-pill,
.topbar .session-pill,
.topbar .identity-pill,
.topbar .user-pill,
.topbar .active-role-pill {
  display:inline-flex !important;
  align-items:center !important;
  justify-content:center !important;
  min-height:30px !important;
  padding:.34rem .78rem !important;
  border-radius:999px !important;
  background:#1d4ed8 !important;
  color:#fff !important;
  border:1px solid rgba(255,255,255,.45) !important;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.12), 0 1px 4px rgba(15,23,42,.18) !important;
  font-size:.92rem !important;
  font-weight:900 !important;
  line-height:1.1 !important;
  white-space:nowrap !important;
  text-decoration:none !important;
}
.topbar .lp-role-pill.secondary,
.topbar .lp-role-pill.magasinier,
.topbar .role-pill.magasinier {
  background:#1e40af !important;
}
.topbar .lp-role-pill.warning { background:#f97316 !important; }
'''
for p in [
    "pedashop-app/pedashop/static/pedashop/pedashop.css",
    "system-manager-app/system_manager/static/system_manager/system.css",
    "tpmanager-app/tp_manager/static/tp_manager/tp.css",
    "safety-app/safety_manager/static/safety_manager/base.css",
    "pfmp-app/pfmp_manager/static/pfmp_manager/pfmp.css",
]:
    txt = read(p)
    if txt and "RC12 — pastilles" not in txt:
        write(p, txt.rstrip() + role_css + "\n")

# ---------------------------------------------------------------------------
# Templates : ajout pastilles manquantes dans System/Safety/TP/PFMP
# ---------------------------------------------------------------------------
# System Manager
txt = read("system-manager-app/system_manager/templates/system_manager/base.html")
if txt and "Utilisateur :" not in txt:
    old = "{% if system_current_user %}<a href=\"{% url 'system_logout' %}\">Déconnexion {{ system_current_user.username }}</a>{% else %}<a href=\"{% url 'system_login' %}\">Connexion</a>{% endif %}"
    new = "{% if system_current_user %}<span class=\"lp-role-pill\">Utilisateur : {% if system_current_user.code %}{{ system_current_user.code }}{% else %}{{ system_current_user.username }}{% endif %}</span><a href=\"{% url 'system_logout' %}\">Déconnexion</a>{% else %}<a href=\"{% url 'system_login' %}\">Connexion</a>{% endif %}"
    txt = txt.replace(old, new)
    write("system-manager-app/system_manager/templates/system_manager/base.html", txt)

# Safety Manager
txt = read("safety-app/safety_manager/templates/safety_manager/base.html")
if txt and "Utilisateur :" not in txt:
    old = "{% if safety_current_user %}<a href=\"{% url 'safety_logout' %}\">Déconnexion {{ safety_current_user.username }}</a>{% else %}<a href=\"{% url 'safety_login' %}\">Connexion</a>{% endif %}"
    new = "{% if safety_current_user %}<span class=\"lp-role-pill\">Utilisateur : {% if safety_current_user.code %}{{ safety_current_user.code }}{% else %}{{ safety_current_user.username }}{% endif %}</span><a href=\"{% url 'safety_logout' %}\">Déconnexion</a>{% else %}<a href=\"{% url 'safety_login' %}\">Connexion</a>{% endif %}"
    txt = txt.replace(old, new)
    write("safety-app/safety_manager/templates/safety_manager/base.html", txt)

# TP Manager
txt = read("tpmanager-app/tp_manager/templates/tp_manager/base.html")
if txt and "Professeur :" not in txt and "Élève :" not in txt:
    old = "{% if tp_current_user %}<a href=\"{% url 'tp_logout' %}\">Déconnexion {{ tp_current_user.username }}</a>{% else %}<a href=\"{% url 'tp_login' %}\">Connexion</a>{% endif %}"
    new = "{% if tp_current_user %}<span class=\"lp-role-pill\">{% if tp_current_user.is_admin_like %}Admin{% elif tp_current_user.is_prof_like %}Professeur{% else %}Élève{% endif %} : {% if tp_current_user.code %}{{ tp_current_user.code }}{% else %}{{ tp_current_user.username }}{% endif %}</span><a href=\"{% url 'tp_logout' %}\">Déconnexion</a>{% else %}<a href=\"{% url 'tp_login' %}\">Connexion</a>{% endif %}"
    txt = txt.replace(old, new)
    write("tpmanager-app/tp_manager/templates/tp_manager/base.html", txt)

# PFMP Manager
txt = read("pfmp-app/pfmp_manager/templates/pfmp_manager/base.html")
if txt and "Professeur :" not in txt and "Élève :" not in txt and "Admin :" not in txt:
    old = "{% if pfmp_current_user %}<a href=\"{% url 'pfmp_logout' %}\">Déconnexion {{ pfmp_current_user.code }}</a>{% else %}<a href=\"{% url 'pfmp_login' %}\">Connexion</a>{% endif %}"
    new = "{% if pfmp_current_user %}<span class=\"lp-role-pill\">{% if pfmp_current_user.is_admin_like %}Admin{% elif pfmp_current_user.is_prof_like %}Professeur{% else %}Élève{% endif %} : {% if pfmp_current_user.code %}{{ pfmp_current_user.code }}{% else %}{{ pfmp_current_user.username }}{% endif %}</span><a href=\"{% url 'pfmp_logout' %}\">Déconnexion</a>{% else %}<a href=\"{% url 'pfmp_login' %}\">Connexion</a>{% endif %}"
    txt = txt.replace(old, new)
    write("pfmp-app/pfmp_manager/templates/pfmp_manager/base.html", txt)

# ---------------------------------------------------------------------------
# PedaShop : bons/nouveau pleine largeur + 30/70 plus strict
# ---------------------------------------------------------------------------
txt = read("pedashop-app/pedashop/templates/pedashop/bon_create.html")
if txt:
    if "bon-create-rc12-fullwidth" not in txt:
        txt = txt.replace("{% block content %}", "{% block content %}<style>.container{max-width:100%!important;width:100%!important;margin:0!important;padding:18px 24px!important}.bon-create-rc12-fullwidth{width:100%}.bon-layout-30-70{display:grid!important;grid-template-columns:30% 70%!important;gap:16px!important;align-items:start!important}.bon-layout-30-70>.card{min-width:0!important}@media(max-width:1050px){.bon-layout-30-70{grid-template-columns:1fr!important}}</style><div class=\"bon-create-rc12-fullwidth\">", 1)
        txt = txt.replace("{% endblock %}", "</div>{% endblock %}")
    txt = txt.replace("class=\"bon-layout-30-70\"", "class=\"bon-layout-30-70\"")
    write("pedashop-app/pedashop/templates/pedashop/bon_create.html", txt)

# ---------------------------------------------------------------------------
# PFMP carte : CSS Leaflet local minimal + invalidateSize renforcé
# ---------------------------------------------------------------------------
pfmp_css_path = "pfmp-app/pfmp_manager/static/pfmp_manager/pfmp.css"
txt = read(pfmp_css_path)
leaflet_css = r'''

/* RC12 — fallback local Leaflet : corrige les tuiles affichées en colonnes si le CSS CDN ne charge pas */
.leaflet-map{width:100%!important;height:590px!important;min-height:590px!important;display:block!important;}
.leaflet-container{height:100%;width:100%;position:relative;overflow:hidden;outline:0;background:#ddd;}
.leaflet-pane,.leaflet-tile,.leaflet-marker-icon,.leaflet-marker-shadow,.leaflet-tile-container,.leaflet-pane>svg,.leaflet-pane>canvas,.leaflet-zoom-box,.leaflet-image-layer,.leaflet-layer{position:absolute;left:0;top:0;}
.leaflet-tile{width:256px;height:256px;user-select:none;-webkit-user-drag:none;}
.leaflet-tile-container{pointer-events:none;}
.leaflet-marker-icon,.leaflet-marker-shadow{display:block;}
.leaflet-control-container .leaflet-top,.leaflet-control-container .leaflet-bottom{position:absolute;z-index:1000;pointer-events:none;}
.leaflet-top{top:0}.leaflet-right{right:0}.leaflet-bottom{bottom:0}.leaflet-left{left:0}
.leaflet-control{position:relative;z-index:800;pointer-events:auto;float:left;clear:both;margin:10px;}
.leaflet-right .leaflet-control{float:right}.leaflet-bottom .leaflet-control{margin-bottom:10px}
.leaflet-popup{position:absolute;text-align:center;margin-bottom:20px;}.leaflet-popup-content-wrapper{background:#fff;border-radius:12px;padding:1px;box-shadow:0 3px 14px rgba(0,0,0,.25)}.leaflet-popup-content{margin:13px 19px;line-height:1.4}.leaflet-popup-tip-container{width:40px;height:20px;position:absolute;left:50%;margin-left:-20px;overflow:hidden;pointer-events:none}.leaflet-popup-tip{width:17px;height:17px;padding:1px;margin:-10px auto 0;background:#fff;transform:rotate(45deg);box-shadow:0 3px 14px rgba(0,0,0,.25)}
@media(max-width:1000px){.leaflet-map{height:430px!important;min-height:430px!important}}
'''
if txt and "RC12 — fallback local Leaflet" not in txt:
    write(pfmp_css_path, txt.rstrip() + leaflet_css + "\n")

map_path = "pfmp-app/pfmp_manager/templates/pfmp_manager/map.html"
txt = read(map_path)
if txt:
    if "forceLeafletResize" not in txt:
        txt = txt.replace("  function initMap() {", "  function forceLeafletResize() {\n    if (!map || !map.invalidateSize) return;\n    map.invalidateSize(true);\n    setTimeout(function(){ map.invalidateSize(true); }, 250);\n    setTimeout(function(){ map.invalidateSize(true); }, 800);\n  }\n\n  function initMap() {", 1)
        txt = txt.replace("    render();\n  }", "    render();\n    forceLeafletResize();\n    window.addEventListener('resize', forceLeafletResize);\n  }", 1)
    write(map_path, txt)

# ---------------------------------------------------------------------------
# Script de réparation routes après coupure WSL / Docker sans supprimer volumes
# ---------------------------------------------------------------------------
repair = root / "scripts/repair_routes_after_wsl.sh"
repair.parent.mkdir(parents=True, exist_ok=True)
repair.write_text(r'''#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
COMPOSE=(docker compose -f "$ROOT_DIR/docker-compose.yml" --env-file "$ROOT_DIR/.env")

echo "[LP Suite] Réparation routes après coupure WSL/Docker — aucun volume supprimé"
"${COMPOSE[@]}" up -d postgres || true
"${COMPOSE[@]}" up -d --build lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app lp-gateway

echo "[LP Suite] Migrations rapides"
for svc in lp-core-app toolmag-app safety-app pedashop-app system-manager-app tpmanager-app pfmp-app; do
  echo "===== migrate $svc ====="
  "${COMPOSE[@]}" run --rm "$svc" python manage.py migrate || true
  echo "===== collectstatic $svc ====="
  "${COMPOSE[@]}" run --rm "$svc" python manage.py collectstatic --noinput || true
done

echo "[LP Suite] Redémarrage gateway"
"${COMPOSE[@]}" restart lp-gateway
"${COMPOSE[@]}" ps

echo "[LP Suite] Contrôle routes"
for url in \
  http://localhost:9000/ \
  http://localhost:9000/toolmag/ \
  http://localhost:9000/safety/ \
  http://localhost:9000/pedashop/ \
  http://localhost:9000/system/ \
  http://localhost:9000/tpmanager/ \
  http://localhost:9000/pfmp/
do
  echo
  echo "===== $url ====="
  curl -sSI "$url" | grep -Ei 'HTTP/|location:|x-lp-gateway-module' || true
done
''', encoding='utf-8')
repair.chmod(0o755)

# Documentation courte
notes = root / "docs/RC12_UI_DROITS_ROUTES_PFMP.md"
notes.parent.mkdir(parents=True, exist_ok=True)
notes.write_text(f"""# {version} — UI, droits par lot, PFMP carte, réparation routes\n\n## Points corrigés\n\n- LP Core : `CoreUser.rights` passe en `TextField` pour éviter l'erreur `value too long for type character varying(255)`.\n- LP Core : gestion par lot avec action `Modifier rôle principal`.\n- LP Core : ajout des droits PFMP dans la page de gestion par lot.\n- LP Core : page `/droits-par-lot/` en largeur 100 %.\n- PedaShop : page `/pedashop/bons/nouveau/` en largeur 100 %, disposition 30 % recherche / 70 % bon.\n- Tous modules : pastilles de connexion harmonisées type ToolMag.\n- PFMP : correction de l'affichage carte Leaflet lorsque le CSS CDN ne se charge pas correctement.\n- Ajout `scripts/repair_routes_after_wsl.sh` pour relancer les routes après coupure WSL sans supprimer les volumes.\n\n## Déploiement\n\nUpgrade semi-rapide obligatoire : migration LP Core.\n\n```bash\nlp-suite upgrade rc\n```\n\nAprès une coupure sauvage WSL :\n\n```bash\ncd /home/user/docker/lp-gestion-atelier/lp-gestion-atelier-ep-suite-rc\n./scripts/repair_routes_after_wsl.sh\n```\n""", encoding='utf-8')
PY

# Recalcul CHECKSUMS si présent
if [[ -f CHECKSUMS.sha256 ]]; then
  find . -type f \
    ! -path './.git/*' \
    ! -path './postgres-db/*' \
    ! -path './lp-core-db/*' \
    ! -path './toolmag-db/*' \
    ! -path './safety-db/*' \
    ! -path './pedashop-db/*' \
    ! -path './system-manager-db/*' \
    ! -path './tpmanager-db/*' \
    ! -path './pfmp-db/*' \
    ! -path './backups/*' \
    ! -path './ssl/*' \
    ! -path './imports/*' \
    ! -name 'CHECKSUMS.sha256' \
    -print0 | sort -z | xargs -0 sha256sum > CHECKSUMS.sha256
fi

echo "Patch ${VERSION} appliqué."
