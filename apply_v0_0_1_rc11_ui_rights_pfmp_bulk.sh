#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re, json, datetime

ROOT = Path('.')
VERSION = 'V0.0.1-RC11'


def p(path: str) -> Path:
    return ROOT / path


def read(path: str) -> str:
    f = p(path)
    if not f.exists():
        print(f'[WARN] fichier absent: {path}')
        return ''
    return f.read_text(encoding='utf-8')


def write(path: str, text: str):
    f = p(path)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding='utf-8')
    print(f'[OK] écrit: {path}')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    print(f'[WARN] motif non trouvé: {label}')
    return text


def append_once(path: str, marker: str, snippet: str):
    text = read(path)
    if not text:
        return
    if marker not in text:
        text = text.rstrip() + "\n\n" + snippet.strip() + "\n"
        write(path, text)
    else:
        print(f'[OK] déjà présent: {marker} dans {path}')


def set_version_files():
    for path in ['VERSION', 'VERSION.txt', '.suite-target-version']:
        if p(path).exists():
            write(path, VERSION + '\n')
    mf = p('manifest.json')
    if mf.exists():
        try:
            data = json.loads(mf.read_text(encoding='utf-8'))
            data['version'] = VERSION
            mf.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print('[OK] manifest.json mis à jour')
        except Exception as exc:
            print(f'[WARN] manifest.json non modifié: {exc}')


# ---------------------------------------------------------------------------
# LP Core — droits longs + rôle par lot
# ---------------------------------------------------------------------------

def patch_lpcore_rights_and_bulk_roles():
    path = 'lp-core-app/core/models.py'
    text = read(path)
    if text:
        text = text.replace(
            "rights = models.CharField(max_length=255, blank=True, help_text='Droits séparés par ;')",
            "rights = models.TextField(blank=True, help_text='Droits séparés par ;')"
        )
        write(path, text)

    mig_dir = p('lp-core-app/core/migrations')
    if mig_dir.exists():
        existing = sorted([m for m in mig_dir.glob('[0-9][0-9][0-9][0-9]_*.py') if m.name != '__init__.py'])
        if not any('rights_textfield' in m.name for m in existing):
            if existing:
                last = existing[-1]
                try:
                    next_no = int(last.name.split('_', 1)[0]) + 1
                    dep = last.stem
                except Exception:
                    next_no = 1
                    dep = None
            else:
                next_no, dep = 1, None
            migration_name = f'{next_no:04d}_coreuser_rights_textfield.py'
            if dep:
                dependencies = f"        ('core', '{dep}'),"
            else:
                dependencies = ""
            migration = f"""from django.db import migrations, models\n\n\nclass Migration(migrations.Migration):\n\n    dependencies = [\n{dependencies}\n    ]\n\n    operations = [\n        migrations.AlterField(\n            model_name='coreuser',\n            name='rights',\n            field=models.TextField(blank=True, help_text='Droits séparés par ;'),\n        ),\n    ]\n"""
            write(str(mig_dir / migration_name), migration)
        else:
            print('[OK] migration rights_textfield déjà présente')

    path = 'lp-core-app/core/views.py'
    text = read(path)
    if text:
        text = text.replace(
            "                    u.rights = ';'.join(sorted(rights))\n                    u.save(update_fields=['rights', 'updated_at'])",
            "                    clean_rights = sorted({r.strip() for r in rights if r and r.strip()})\n                    u.rights = ';'.join(clean_rights)\n                    u.save(update_fields=['rights', 'updated_at'])"
        )
        marker = "        elif action == 'set_role':"
        if marker not in text:
            text = text.replace(
                "        elif action in {'add_store', 'remove_store'}:",
                "        elif action == 'set_role':\n            target_role = request.POST.get('target_role')\n            allowed_roles = {code for code, _label in CoreUser.ROLE_CHOICES}\n            if target_role in allowed_roles:\n                count = target_qs.count()\n                for u in target_qs:\n                    u.role_principal = target_role\n                    u.save(update_fields=['role_principal', 'updated_at'])\n                messages.success(request, f'Rôle principal mis à jour sur {count} utilisateur(s).')\n                log_core_action(actor, 'SET_ROLE_BULK', 'bulk', target_role)\n            else:\n                messages.error(request, 'Rôle principal invalide ou non renseigné.')\n        elif action in {'add_store', 'remove_store'}:",
                1
            )
        write(path, text)

    path = 'lp-core-app/core/templates/core/bulk_permissions.html'
    text = read(path)
    if text:
        text = text.replace(
            "<li><strong>Droits</strong> : ajout ou retrait des codes de droits consommés par les modules.</li>",
            "<li><strong>Droits</strong> : ajout ou retrait des codes de droits consommés par les modules.</li>\n    <li><strong>Rôle principal</strong> : modifie le rôle de base LP Core : élève, utilisateur, magasinier, professeur, responsable ou administrateur.</li>"
        )
        text = text.replace(
            "<option value=\"remove_right\">Retirer droit</option><option value=\"add_store\">Affecter magasin</option>",
            "<option value=\"remove_right\">Retirer droit</option><option value=\"set_role\">Modifier rôle principal</option><option value=\"add_store\">Affecter magasin</option>"
        )
        if 'data-actions="set_role"' not in text:
            insert = """
    <div class="bulk-block" data-actions="set_role">
      <h3>Rôle principal</h3>
      <p class="muted">Le rôle principal sert de base aux modules. Les droits détaillés restent gérés séparément.</p>
      <label>Nouveau rôle
        <select name="target_role">
          {% for code,label in roles %}<option value="{{ code }}">{{ label }}</option>{% endfor %}
        </select>
      </label>
    </div>
"""
            text = text.replace("\n    <div class=\"bulk-block\" data-actions=\"add_store remove_store\">", insert + "\n    <div class=\"bulk-block\" data-actions=\"add_store remove_store\">", 1)
        write(path, text)


# ---------------------------------------------------------------------------
# CSS commun : pastilles de connexion type ToolMag
# ---------------------------------------------------------------------------

ROLE_PILL_CSS = r"""
/* V0.0.1-RC11 — pastilles de connexion harmonisées type ToolMag */
.lp-role-pill{
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  gap:.35rem!important;
  min-height:30px!important;
  padding:.34rem .78rem!important;
  border-radius:999px!important;
  background:#1d4ed8!important;
  color:#fff!important;
  border:1px solid rgba(255,255,255,.55)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.24),0 1px 4px rgba(15,23,42,.25)!important;
  font-size:.92rem!important;
  font-weight:900!important;
  line-height:1!important;
  text-decoration:none!important;
  white-space:nowrap!important;
  opacity:1!important;
}
.lp-role-pill.active{background:#2563eb!important;border-color:#bfdbfe!important;}
.lp-role-pill.secondary{background:#0f3f78!important;}
.lp-role-pill:hover{filter:brightness(1.05);text-decoration:none!important;}
"""

PFMP_MAP_CSS = r"""
/* V0.0.1-RC11 — correctif carte PFMP / Leaflet local minimal */
.leaflet-map{width:100%!important;height:590px!important;min-height:590px!important;position:relative!important;overflow:hidden!important;background:#e8f1f3!important;}
.leaflet-container{width:100%!important;height:100%!important;position:relative!important;overflow:hidden!important;outline:0!important;}
.leaflet-pane,.leaflet-tile,.leaflet-marker-icon,.leaflet-marker-shadow,.leaflet-tile-container,.leaflet-pane>svg,.leaflet-pane>canvas,.leaflet-zoom-box,.leaflet-image-layer,.leaflet-layer{position:absolute!important;left:0;top:0;}
.leaflet-tile{max-width:none!important;max-height:none!important;user-select:none!important;pointer-events:none!important;}
.leaflet-container img.leaflet-tile{max-width:none!important;}
.leaflet-control-container .leaflet-top,.leaflet-control-container .leaflet-bottom{position:absolute!important;z-index:1000!important;pointer-events:none!important;}
.leaflet-control-container .leaflet-top{top:0!important}.leaflet-control-container .leaflet-right{right:0!important}.leaflet-control-container .leaflet-bottom{bottom:0!important}.leaflet-control-container .leaflet-left{left:0!important}
.leaflet-control{position:relative!important;z-index:1000!important;pointer-events:auto!important;float:left!important;clear:both!important;}
@media(max-width:1000px){.leaflet-map{height:430px!important;min-height:430px!important;}}
"""


def append_role_css():
    for path in [
        'pedashop-app/pedashop/static/pedashop/pedashop.css',
        'system-manager-app/system_manager/static/system_manager/system.css',
        'tpmanager-app/tp_manager/static/tp_manager/tp.css',
        'safety-app/safety_manager/static/safety_manager/base.css',
        'pfmp-app/pfmp_manager/static/pfmp_manager/pfmp.css',
    ]:
        append_once(path, 'V0.0.1-RC11 — pastilles de connexion', ROLE_PILL_CSS)
    append_once('pfmp-app/pfmp_manager/static/pfmp_manager/pfmp.css', 'V0.0.1-RC11 — correctif carte PFMP', PFMP_MAP_CSS)


def patch_pfmp_css_topbar():
    path = 'pfmp-app/pfmp_manager/static/pfmp_manager/pfmp.css'
    text = read(path)
    if not text:
        return
    extra = r"""
/* V0.0.1-RC11 — PFMP bandeau harmonisé avec les autres modules */
.topbar{background:#0b2d4d!important;color:#fff!important;border-bottom:0!important;box-shadow:0 3px 10px rgba(0,0,0,.12)!important;}
.brand span{display:inline-block!important;padding:.22rem .55rem!important;border-radius:999px!important;background:#eff6ff!important;color:#083665!important;font-size:.78rem!important;font-weight:900!important;white-space:nowrap!important;}
nav a,summary{color:#fff!important;font-weight:800!important;}
nav a:hover,summary:hover{background:rgba(255,255,255,.12)!important;}
details div a{color:#083665!important;}
"""
    if 'PFMP bandeau harmonisé' not in text:
        write(path, text.rstrip() + '\n\n' + extra.strip() + '\n')


# ---------------------------------------------------------------------------
# PedaShop — mode utilisateur/magasinier + menus/pastilles + bon dynamique
# ---------------------------------------------------------------------------

def patch_pedashop():
    path = 'pedashop-app/pedashop/views.py'
    text = read(path)
    if text:
        if 'def switch_mode_view(request, mode):' not in text:
            text = text.replace(
                "def logout_view(request):\n    request.session.pop('pedashop_user_id', None)\n    request.session.pop('pedashop_active_role', None)\n    return redirect('pedashop_login')",
                "def logout_view(request):\n    request.session.pop('pedashop_user_id', None)\n    request.session.pop('pedashop_active_role', None)\n    return redirect('pedashop_login')\n\n\ndef switch_mode_view(request, mode):\n    user = require_login(request)\n    if not user:\n        return redirect('pedashop_login')\n    if mode not in {'utilisateur', 'magasinier'}:\n        messages.error(request, 'Mode PedaShop invalide.')\n        return redirect('pedashop_dashboard')\n    if mode == 'magasinier' and not user.is_storekeeper_like:\n        messages.error(request, 'Ce compte n’a pas le droit magasinier PedaShop.')\n        return redirect('pedashop_dashboard')\n    request.session['pedashop_active_role'] = mode\n    messages.success(request, f'Mode PedaShop actif : {mode}.')\n    return redirect(request.META.get('HTTP_REFERER') or 'pedashop_dashboard')"
            )
        write(path, text)

    path = 'pedashop-app/pedashop/urls.py'
    text = read(path)
    if text and "pedashop_switch_mode" not in text:
        text = text.replace("    path('logout/', views.logout_view, name='pedashop_logout'),", "    path('logout/', views.logout_view, name='pedashop_logout'),\n    path('switch-mode/<str:mode>/', views.switch_mode_view, name='pedashop_switch_mode'),")
        write(path, text)

    path = 'pedashop-app/pedashop/templates/pedashop/base.html'
    text = read(path)
    if text:
        text = text.replace("    {% if pedashop_current_user %}<span class=\"role-pill\">{{ request.session.pedashop_active_role|default:'utilisateur' }}</span>{% endif %}\n", "")
        old = "{% if pedashop_current_user %}<a href=\"{% url 'pedashop_logout' %}\">Déconnexion {{ pedashop_current_user.username }}</a>{% else %}<a href=\"{% url 'pedashop_login' %}\">Connexion</a>{% endif %}"
        new = """{% if pedashop_current_user %}
      <a class="lp-role-pill {% if request.session.pedashop_active_role == 'utilisateur' or not request.session.pedashop_active_role %}active{% endif %}" href="{% url 'pedashop_switch_mode' 'utilisateur' %}">Utilisateur : {{ pedashop_current_user.code|default:pedashop_current_user.username }}</a>
      {% if pedashop_current_user.is_storekeeper_like %}<a class="lp-role-pill secondary {% if request.session.pedashop_active_role == 'magasinier' %}active{% endif %}" href="{% url 'pedashop_switch_mode' 'magasinier' %}">Magasinier : {{ pedashop_current_user.code|default:pedashop_current_user.username }}</a>{% endif %}
      <a href="{% url 'pedashop_logout' %}">Déconnexion</a>
    {% else %}<a href="{% url 'pedashop_login' %}">Connexion</a>{% endif %}"""
        text = text.replace(old, new)
        write(path, text)

    path = 'pedashop-app/pedashop/templates/pedashop/bon_create.html'
    if p(path).exists():
        bon_tpl = r"""{% extends 'pedashop/base.html' %}
{% block content %}
<h1>Créer une demande / bon multi-articles</h1>
<div class="bon-create-layout">
  <section class="card bon-search-panel">
    <h2>1. Recherche article</h2>
    <p class="muted">Recherche dynamique par code produit, référence fabricant, désignation, EAN ou code-barres scannette.</p>
    <label>Article / code-barres
      <input id="article-search" type="text" autocomplete="off" placeholder="Scanner ou saisir code, référence, désignation">
    </label>
    <div id="article-suggestions" class="suggestion-box"></div>
    <form method="post" id="add-selected-form" class="selected-article-card" style="display:none">
      {% csrf_token %}
      <input type="hidden" name="action" value="add_line">
      <input type="hidden" name="article_id" id="selected-article-id">
      <h3 id="selected-article-label"></h3>
      <p class="muted" id="selected-article-meta"></p>
      <label>Quantité <input name="quantite" value="1" type="number" step="0.01" min="0.01"></label>
      <label>Type de sortie
        <select name="type_sortie" class="type-sortie"><option value="definitive">Définitive</option><option value="temporaire">Temporaire avec retour</option></select>
      </label>
      <label class="date-retour-wrap">Date de retour prévue <input type="date" name="date_retour_prevue" class="date-retour"></label>
      <label>Commentaire ligne <input name="commentaire_ligne"></label>
      <button class="btn primary" type="submit">Ajouter au bon</button>
    </form>
    <details class="advanced-search"><summary>Recherche classique avancée</summary>
      <form method="get" class="filterbar">{{ search_form.as_p }}<button class="btn" type="submit">Rechercher</button></form>
      <div class="table-wrap"><table><thead><tr><th>Article</th><th>Stock</th><th>Choisir</th></tr></thead><tbody>{% for s in results %}<tr><td><b>{{ s.article.reference_interne }}</b><br>{{ s.article.designation }}</td><td>{{ s.magasin.code }} : {{ s.stock_disponible }} dispo</td><td><button class="btn small" type="button" onclick="selectArticle({{ s.article.id }}, '{{ s.article.reference_interne|escapejs }}', '{{ s.article.designation|escapejs }}', '{{ s.article.reference_fabricant|escapejs }}')">Choisir</button></td></tr>{% empty %}<tr><td colspan="3">Aucun résultat.</td></tr>{% endfor %}</tbody></table></div>
    </details>
  </section>
  <section class="card bon-current-panel">
    <h2>2. Bon en cours</h2>
    <form method="post" id="header-form">{% csrf_token %}<input type="hidden" name="action" value="submit_bon"><div class="form-grid">{{ header_form.as_p }}</div><h3>Articles ajoutés</h3><table><thead><tr><th>Article</th><th>Qté</th><th>Sortie</th><th>Retour</th></tr></thead><tbody>{% for c in cart %}<tr><td>{{ c.article_label }}</td><td>{{ c.quantite }}</td><td>{{ c.type_sortie }}</td><td>{{ c.date_retour_prevue }}</td></tr>{% empty %}<tr><td colspan="4">Aucun article ajouté.</td></tr>{% endfor %}</tbody></table><div class="actions"><button class="btn primary" type="submit">Valider le bon</button></div></form>
    <form method="post">{% csrf_token %}<input type="hidden" name="action" value="clear_cart"><button class="btn" type="submit">Vider le bon</button></form>
  </section>
</div>
<script>
function syncHeader(form){['id_type_bon','id_magasin','id_professeur_responsable','id_nom_tp','id_classe_ou_groupe','id_commentaire'].forEach(function(id){var el=document.getElementById(id); if(el){var i=document.createElement('input'); i.type='hidden'; i.name=el.name; i.value=el.value; form.appendChild(i);}})}
function selectArticle(id, ref, designation, referenceFabricant){document.getElementById('selected-article-id').value=id;document.getElementById('selected-article-label').textContent=ref+' — '+designation;document.getElementById('selected-article-meta').textContent=referenceFabricant || '';document.getElementById('add-selected-form').style.display='grid';}
const search=document.getElementById('article-search'); const box=document.getElementById('article-suggestions'); let timer=null;
search.addEventListener('input', function(){clearTimeout(timer); const q=this.value.trim(); if(!q){box.innerHTML=''; return;} timer=setTimeout(function(){fetch('{% url 'pedashop_api_article_search' %}?q='+encodeURIComponent(q)).then(r=>r.json()).then(data=>{box.innerHTML=''; (data.results||[]).forEach(a=>{const b=document.createElement('button'); b.type='button'; b.className='suggestion-row'; b.innerHTML='<b>'+a.reference_interne+'</b> — '+a.designation+'<br><small>'+(a.reference_fabricant||'')+' '+(a.code_ean||'')+'</small>'; b.onclick=function(){selectArticle(a.id,a.reference_interne,a.designation,a.reference_fabricant); box.innerHTML=''; search.value=a.reference_interne;}; box.appendChild(b);});});},160);});
document.getElementById('add-selected-form').addEventListener('submit',function(e){var type=this.querySelector('.type-sortie').value; var date=this.querySelector('.date-retour'); if(type==='temporaire' && !date.value){e.preventDefault(); alert('Date de retour obligatoire pour une sortie temporaire.'); return false;} syncHeader(this);});
document.querySelectorAll('.type-sortie').forEach(function(sel){function upd(){var form=sel.closest('form'); var date=form.querySelector('.date-retour'); var wrap=form.querySelector('.date-retour-wrap'); if(sel.value==='temporaire'){if(wrap)wrap.style.display='block'; date.required=true;} else {if(wrap)wrap.style.display='none'; date.required=false; date.value='';}} sel.addEventListener('change',upd); upd();});
</script>
{% endblock %}
"""
        write(path, bon_tpl)

    append_once('pedashop-app/pedashop/static/pedashop/pedashop.css', 'V0.0.1-RC11 — bon dynamique 30/70', r"""
/* V0.0.1-RC11 — bon dynamique 30/70 */
.bon-create-layout{width:100%;display:grid;grid-template-columns:30% minmax(0,70%);gap:16px;align-items:start}.bon-search-panel,.bon-current-panel{min-width:0}.selected-article-card{display:grid;gap:.65rem;margin-top:1rem;border:1px solid #bfdbfe;background:#eff6ff;border-radius:14px;padding:1rem}.advanced-search{margin-top:1rem}.advanced-search summary{font-weight:900;cursor:pointer}.date-retour-wrap{display:none}@media(max-width:980px){.bon-create-layout{grid-template-columns:1fr}}
""")

    path = 'pedashop-app/pedashop/templates/pedashop/magasin_list.html'
    if p(path).exists():
        tpl = r"""{% extends 'pedashop/base.html' %}
{% block content %}<h1>Magasins</h1><div class="actions"><a class="btn primary" href="{% url 'pedashop_magasin_create' %}">Nouveau magasin</a></div><form method="post" action="{% url 'pedashop_magasin_bulk_delete' %}" onsubmit="return confirm('Confirmer la suppression/désactivation des magasins cochés ?');">{% csrf_token %}<div class="card table-wrap"><table><thead><tr><th><input type="checkbox" onclick="document.querySelectorAll('.store-check').forEach(c=>c.checked=this.checked)"></th><th>Code</th><th>Nom</th><th>Responsable</th><th>Actif</th></tr></thead><tbody>{% for i in items %}<tr><td><input class="store-check" type="checkbox" name="magasins" value="{{ i.pk }}"></td><td>{{ i.code }}</td><td>{{ i.nom }}</td><td>{{ i.responsable }}</td><td>{{ i.actif|yesno:'Oui,Non' }}</td></tr>{% empty %}<tr><td colspan="5">Aucun magasin.</td></tr>{% endfor %}</tbody></table></div><div class="actions"><button class="btn danger" type="submit">Supprimer / désactiver les magasins cochés</button></div></form>{% endblock %}
"""
        write(path, tpl)

    path = 'pedashop-app/pedashop/views.py'
    text = read(path)
    if text and 'def magasin_bulk_delete' not in text:
        insert = r'''
@require_http_methods(['POST'])
def magasin_bulk_delete(request):
    user = require_admin(request)
    if not user:
        return redirect('pedashop_login')
    ids = request.POST.getlist('magasins')
    deleted = 0
    disabled = 0
    for magasin in Magasin.objects.filter(id__in=ids):
        try:
            used = (
                magasin.stocks.exists() or magasin.bons.exists() or magasin.projections.exists() or
                magasin.reservations.exists() or magasin.mouvements_sortants.exists() or magasin.mouvements_entrants.exists()
            )
        except Exception:
            used = True
        if used:
            magasin.actif = False
            magasin.save(update_fields=['actif'])
            disabled += 1
        else:
            magasin.delete()
            deleted += 1
    messages.success(request, f'Magasins traités : {deleted} supprimé(s), {disabled} désactivé(s) car liés à l’historique.')
    return redirect('pedashop_magasin_list')

'''
        text = text.replace("\ndef emplacement_list(request):", "\n" + insert + "\ndef emplacement_list(request):", 1)
        write(path, text)

    path = 'pedashop-app/pedashop/urls.py'
    text = read(path)
    if text and 'pedashop_magasin_bulk_delete' not in text:
        text = text.replace("    path('magasins/<int:pk>/modifier/', views.magasin_form, name='pedashop_magasin_edit'),", "    path('magasins/<int:pk>/modifier/', views.magasin_form, name='pedashop_magasin_edit'),\n    path('magasins/supprimer-selection/', views.magasin_bulk_delete, name='pedashop_magasin_bulk_delete'),")
        write(path, text)


# ---------------------------------------------------------------------------
# Autres modules — pastilles role dans les bases
# ---------------------------------------------------------------------------

def patch_other_base_templates():
    # System Manager
    path = 'system-manager-app/system_manager/templates/system_manager/base.html'
    text = read(path)
    if text and 'Utilisateur : {{ system_current_user' not in text:
        text = text.replace(
            "{% if system_current_user %}<a href=\"{% url 'system_logout' %}\">Déconnexion {{ system_current_user.username }}</a>{% else %}<a href=\"{% url 'system_login' %}\">Connexion</a>{% endif %}",
            "{% if system_current_user %}<span class=\"lp-role-pill active\">Utilisateur : {{ system_current_user.code|default:system_current_user.username }}</span><a href=\"{% url 'system_logout' %}\">Déconnexion</a>{% else %}<a href=\"{% url 'system_login' %}\">Connexion</a>{% endif %}"
        )
        write(path, text)

    # TP Manager
    path = 'tpmanager-app/tp_manager/templates/tp_manager/base.html'
    text = read(path)
    if text and 'tp-role-pill' not in text:
        text = text.replace(
            "{% if tp_current_user %}<a href=\"{% url 'tp_logout' %}\">Déconnexion {{ tp_current_user.username }}</a>{% else %}<a href=\"{% url 'tp_login' %}\">Connexion</a>{% endif %}",
            "{% if tp_current_user %}<span class=\"lp-role-pill active tp-role-pill\">{% if tp_current_user.is_admin_like %}Admin{% elif tp_current_user.is_prof_like %}Professeur{% else %}Élève{% endif %} : {{ tp_current_user.code|default:tp_current_user.username }}</span><a href=\"{% url 'tp_logout' %}\">Déconnexion</a>{% else %}<a href=\"{% url 'tp_login' %}\">Connexion</a>{% endif %}"
        )
        write(path, text)

    # Safety Manager
    path = 'safety-app/safety_manager/templates/safety_manager/base.html'
    text = read(path)
    if text and 'safety-role-pill' not in text:
        text = text.replace(
            "{% if safety_current_user %}<a href=\"{% url 'safety_logout' %}\">Déconnexion {{ safety_current_user.username }}</a>{% else %}<a href=\"{% url 'safety_login' %}\">Connexion</a>{% endif %}",
            "{% if safety_current_user %}<span class=\"lp-role-pill active safety-role-pill\">Utilisateur : {{ safety_current_user.code|default:safety_current_user.username }}</span><a href=\"{% url 'safety_logout' %}\">Déconnexion</a>{% else %}<a href=\"{% url 'safety_login' %}\">Connexion</a>{% endif %}"
        )
        write(path, text)

    # PFMP Manager
    path = 'pfmp-app/pfmp_manager/templates/pfmp_manager/base.html'
    text = read(path)
    if text and 'pfmp-role-pill' not in text:
        text = text.replace(
            "{% if pfmp_current_user %}<a href=\"{% url 'pfmp_logout' %}\">Déconnexion {{ pfmp_current_user.code }}</a>{% else %}<a href=\"{% url 'pfmp_login' %}\">Connexion</a>{% endif %}",
            "{% if pfmp_current_user %}<span class=\"lp-role-pill active pfmp-role-pill\">{% if pfmp_current_user.is_admin_like %}Admin{% elif pfmp_current_user.is_prof_like %}Professeur{% else %}Élève{% endif %} : {{ pfmp_current_user.code|default:pfmp_current_user.username }}</span><a href=\"{% url 'pfmp_logout' %}\">Déconnexion</a>{% else %}<a href=\"{% url 'pfmp_login' %}\">Connexion</a>{% endif %}"
        )
        write(path, text)


def patch_pfmp_map():
    path = 'pfmp-app/pfmp_manager/templates/pfmp_manager/map.html'
    text = read(path)
    if not text:
        return
    if 'pfmp-map-invalidate-size' not in text:
        text = text.replace(
            "    map.on('click', function (event) { setOrigin(event.latlng.lat, event.latlng.lng); });\n    render();",
            "    map.on('click', function (event) { setOrigin(event.latlng.lat, event.latlng.lng); });\n    render();\n    // pfmp-map-invalidate-size : correction affichage tuiles Leaflet quand la carte est initialisée dans un layout responsive.\n    setTimeout(function(){ map.invalidateSize(); }, 150);\n    setTimeout(function(){ map.invalidateSize(); }, 600);\n    window.addEventListener('resize', function(){ map.invalidateSize(); });"
        )
        write(path, text)


# ---------------------------------------------------------------------------
# Sécurité : checksums
# ---------------------------------------------------------------------------

set_version_files()
patch_lpcore_rights_and_bulk_roles()
append_role_css()
patch_pfmp_css_topbar()
patch_pedashop()
patch_other_base_templates()
patch_pfmp_map()

print('\n[RC11] Patch appliqué. Lance ensuite les migrations puis rebuild.')
PY

# Recalcul checksum si présent.
if [ -f CHECKSUMS.sha256 ]; then
  tmpfile="$(mktemp)"
  find . -type f \
    ! -path './.git/*' \
    ! -path './postgres-db/*' \
    ! -path './backups/*' \
    ! -path './ssl/*' \
    ! -path './media/*' \
    ! -name 'CHECKSUMS.sha256' \
    -print0 | sort -z | xargs -0 sha256sum > "$tmpfile"
  mv "$tmpfile" CHECKSUMS.sha256
  echo '[OK] CHECKSUMS.sha256 recalculé'
fi

echo
cat <<'EOF'
RC11 appliqué.
Contrôles conseillés :
  cat VERSION VERSION.txt
  sha256sum -c CHECKSUMS.sha256 2>&1 | grep -E 'FAILED|WARNING|No such file|did NOT match' || echo 'CHECKSUMS OK'
  git diff --stat
EOF
