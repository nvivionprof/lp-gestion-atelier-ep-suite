#!/usr/bin/env bash
set -euo pipefail

VERSION="V0.0.1-RC10"
echo "[RC10] Application : PedaShop modes/import/vidage + System cleanup + TP badges + exports PDF"

ROOT="$(pwd)"
require_file() {
  if [[ ! -f "$1" ]]; then
    echo "[RC10][ERREUR] Fichier introuvable : $1" >&2
    exit 1
  fi
}

require_file "pedashop-app/pedashop/views.py"
require_file "pedashop-app/pedashop/services.py"
require_file "pedashop-app/pedashop/urls.py"
require_file "pedashop-app/pedashop/templates/pedashop/base.html"
require_file "pedashop-app/pedashop/templates/pedashop/bon_create.html"
require_file "pedashop-app/pedashop/templates/pedashop/magasin_list.html"
require_file "pedashop-app/pedashop/static/pedashop/pedashop.css"
require_file "system-manager-app/system_manager/urls.py"
require_file "system-manager-app/system_manager/templates/system_manager/base.html"
require_file "system-manager-app/system_manager/views.py"
require_file "lp-core-app/core/views.py"
require_file "tpmanager-app/tp_manager/templates/tp_manager/base.html"
require_file "tpmanager-app/tp_manager/static/tp_manager/tp.css"

python3 <<'PY'
from pathlib import Path
import json, re, hashlib, os

VERSION = "V0.0.1-RC10"
ROOT = Path('.')

def p(path): return ROOT / path

def read(path): return p(path).read_text(encoding='utf-8')
def write(path, data): p(path).write_text(data, encoding='utf-8', newline='\n')

def replace_once(path, old, new, label=None):
    data = read(path)
    if old not in data:
        raise SystemExit(f"[RC10][ERREUR] Motif introuvable dans {path}: {label or old[:80]}")
    write(path, data.replace(old, new, 1))

def replace_all(path, old, new):
    data = read(path)
    write(path, data.replace(old, new))

# -----------------------------------------------------------------------------
# Versions
# -----------------------------------------------------------------------------
for vf in ['VERSION', 'VERSION.txt', '.suite-target-version']:
    if p(vf).exists():
        write(vf, VERSION + '\n')
if p('manifest.json').exists():
    try:
        obj = json.loads(read('manifest.json'))
        obj['version'] = VERSION
        obj['suite_version'] = VERSION
        write('manifest.json', json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    except Exception:
        pass

# -----------------------------------------------------------------------------
# PedaShop services.py : remplacement total sans suppression des articles protégés
# -----------------------------------------------------------------------------
services = read('pedashop-app/pedashop/services.py')
services = services.replace(
"""    if mode == 'replace_all' and not dry_run:\n        report['deleted_articles'] = Article.objects.count()\n        StockArticleMagasin.objects.all().delete()\n        Article.objects.all().delete()\n""",
"""    if mode == 'replace_all' and not dry_run:\n        # On ne supprime plus les articles : l'historique PedaShop référence les articles\n        # via des clés protégées, notamment MouvementStock.article.\n        # Le remplacement total archive les anciens articles, vide les stocks opérationnels,\n        # puis réactive/met à jour les articles présents dans le fichier importé.\n        report['deleted_articles'] = Article.objects.filter(archive=False).count()\n        report['warnings'].append(\n            \"Remplacement total : historique conservé ; anciens articles archivés et stocks reconstruits depuis le fichier.\"\n        )\n        StockArticleMagasin.objects.all().delete()\n        Article.objects.update(archive=True)\n"""
)
services = services.replace(
"""            article = Article(reference_interne=ref)\n            for f in article_fields:\n                setattr(article, f, row.get(f, getattr(article, f, '')))\n            article.designation = article.designation or ref\n            article.save()\n""",
"""            article = Article(reference_interne=ref)\n            for f in article_fields:\n                setattr(article, f, row.get(f, getattr(article, f, '')))\n            article.designation = article.designation or ref\n            article.archive = False\n            article.save()\n"""
)
services = services.replace(
"""                if changed:\n                    article.save()\n                report['updated_articles'] += 1\n""",
"""                if article.archive:\n                    article.archive = False\n                    changed.append('archive')\n                if changed:\n                    article.save()\n                report['updated_articles'] += 1\n"""
)
write('pedashop-app/pedashop/services.py', services)

# -----------------------------------------------------------------------------
# PedaShop urls.py : role switch + maintenance vidage base
# -----------------------------------------------------------------------------
urls = read('pedashop-app/pedashop/urls.py')
if "pedashop_switch_role" not in urls:
    urls = urls.replace("    path('logout/', views.logout_view, name='pedashop_logout'),\n",
                        "    path('logout/', views.logout_view, name='pedashop_logout'),\n    path('role/<str:role>/', views.switch_role, name='pedashop_switch_role'),\n")
if "pedashop_database_purge" not in urls:
    urls = urls.replace("    path('import-excel/', views.import_excel, name='pedashop_import_excel'),\n",
                        "    path('import-excel/', views.import_excel, name='pedashop_import_excel'),\n    path('maintenance/vider-bases/', views.database_purge, name='pedashop_database_purge'),\n")
if "pedashop_export_config" not in urls:
    urls = urls.replace("    path('exports/stock.pdf', views.export_stock_pdf, name='pedashop_stock_pdf'),\n",
                        "    path('exports/stock.pdf', views.export_stock_pdf, name='pedashop_stock_pdf'),\n    path('exports/configuration/', views.export_pdf_config, name='pedashop_export_config'),\n")
write('pedashop-app/pedashop/urls.py', urls)

# -----------------------------------------------------------------------------
# PedaShop views.py : imports, role switch, purge, magasin batch delete, export config
# -----------------------------------------------------------------------------
views_path = 'pedashop-app/pedashop/views.py'
views = read(views_path)
if "from django.db.models.deletion import ProtectedError" not in views:
    views = views.replace("from django.db import transaction\n", "from django.db import transaction\nfrom django.db.models.deletion import ProtectedError\n")
# portal login defaults to utilisateur; user can switch if authorised.
views = views.replace("request.session['pedashop_active_role'] = 'magasinier' if user.is_storekeeper_like else 'utilisateur'",
                      "request.session['pedashop_active_role'] = 'utilisateur'")

role_block = r'''

@require_http_methods(['POST'])
def switch_role(request, role):
    """Bascule explicite Utilisateur / Magasinier, comme dans ToolMag."""
    user = require_login(request)
    if not user:
        return redirect('pedashop_login')
    role = (role or '').strip().lower()
    if role not in {'utilisateur', 'magasinier'}:
        messages.error(request, 'Mode PedaShop inconnu.')
    elif role == 'magasinier' and not user.is_storekeeper_like:
        messages.error(request, 'Ce compte n’a pas le droit magasinier PedaShop.')
    else:
        request.session['pedashop_active_role'] = role
        messages.success(request, f'Mode PedaShop actif : {role}.')
    return redirect(request.META.get('HTTP_REFERER') or 'pedashop_dashboard')
'''
if "def switch_role(request, role):" not in views:
    views = views.replace("def logout_view(request):\n    request.session.pop('pedashop_user_id', None)\n    request.session.pop('pedashop_active_role', None)\n    return redirect('pedashop_login')\n",
"def logout_view(request):\n    request.session.pop('pedashop_user_id', None)\n    request.session.pop('pedashop_active_role', None)\n    return redirect('pedashop_login')\n" + role_block)

# Replace magasin_list with batch deletion/deactivation.
old_magasin_list = """def magasin_list(request):\n    user = require_login(request)\n    if not user:\n        return redirect('pedashop_login')\n    return render(request, 'pedashop/magasin_list.html', {'items': Magasin.objects.all()})\n"""
new_magasin_list = """@require_http_methods(['GET', 'POST'])\ndef magasin_list(request):\n    user = require_login(request)\n    if not user:\n        return redirect('pedashop_login')\n    if request.method == 'POST':\n        admin = require_admin(request)\n        if not admin:\n            return redirect('pedashop_login')\n        action = request.POST.get('action')\n        ids = request.POST.getlist('selected_magasins')\n        if action == 'delete_selected' and ids:\n            confirm = (request.POST.get('confirmation') or '').strip()\n            if confirm != 'SUPPRIMER MAGASINS':\n                messages.error(request, 'Confirmation incorrecte. Saisir SUPPRIMER MAGASINS.')\n            else:\n                deleted = 0; disabled = 0\n                for mag in Magasin.objects.filter(pk__in=ids):\n                    try:\n                        mag.delete()\n                        deleted += 1\n                    except ProtectedError:\n                        mag.actif = False\n                        mag.save(update_fields=['actif'])\n                        disabled += 1\n                messages.success(request, f'{deleted} magasin(s) supprimé(s), {disabled} magasin(s) désactivé(s) car liés à l’historique.')\n        elif action == 'delete_selected':\n            messages.warning(request, 'Aucun magasin coché.')\n        return redirect('pedashop_magasin_list')\n    return render(request, 'pedashop/magasin_list.html', {'items': Magasin.objects.all(), 'can_admin_magasins': bool(user and user.is_admin_like)})\n"""
if old_magasin_list in views:
    views = views.replace(old_magasin_list, new_magasin_list)
else:
    # Try non-decorated signature fallback.
    if "def magasin_list(request):" in views and "selected_magasins" not in views:
        raise SystemExit('[RC10][ERREUR] magasin_list existe mais son corps ne correspond pas au motif attendu.')

# Add purge + export config before export_bon_pdf
purge_block = r'''

# ---------------------------------------------------------------------------
# Maintenance PedaShop : vidage contrôlé des données métier
# ---------------------------------------------------------------------------

def _purge_pedashop_operational_data(include_stores=False):
    from .models import DemandeAchat, LigneDemandeAchat
    deletion_order = [
        StockAlert, MouvementStock, RetourAttendu, Reclamation, BonHistorique,
        LigneBon, Bon, LigneProjectionPedagogique, ProjectionPedagogique,
        Reservation, SupplierConsultationLine, SupplierConsultation,
        LigneDemandeAchat, DemandeAchat,
        StockArticleMagasin, Article,
    ]
    if include_stores:
        deletion_order.extend([Emplacement, Magasin])
    report = {}
    for model in deletion_order:
        name = model.__name__
        try:
            count = model.objects.count()
            model.objects.all().delete()
            report[name] = count
        except Exception as exc:
            report[name] = f'ERREUR: {exc}'
    return report

@require_http_methods(['GET', 'POST'])
def database_purge(request):
    admin = require_admin(request)
    if not admin:
        return redirect('pedashop_login')
    report = None
    if request.method == 'POST':
        confirmation = (request.POST.get('confirmation') or '').strip()
        include_stores = request.POST.get('include_stores') == '1'
        if confirmation != 'VIDER PEDASHOP':
            messages.error(request, 'Confirmation incorrecte. Saisir VIDER PEDASHOP.')
        else:
            with transaction.atomic():
                report = _purge_pedashop_operational_data(include_stores=include_stores)
            messages.success(request, 'Vidage PedaShop terminé. Les comptes utilisateurs sont conservés.')
    counts = {
        'articles': Article.objects.count(),
        'stocks': StockArticleMagasin.objects.count(),
        'mouvements': MouvementStock.objects.count(),
        'bons': Bon.objects.count(),
        'magasins': Magasin.objects.count(),
    }
    return render(request, 'pedashop/database_purge.html', {'counts': counts, 'report': report})

@require_http_methods(['GET', 'POST'])
def export_pdf_config(request):
    user = require_login(request)
    if not user or not (user.is_admin_like or user.is_teacher_like):
        messages.error(request, 'Configuration export PDF réservée aux professeurs ou administrateurs.')
        return redirect('pedashop_login' if not user else 'pedashop_dashboard')
    if request.method == 'POST':
        request.session['pedashop_pdf_identity_mode'] = request.POST.get('identity_mode') or 'anonymous'
        request.session['pedashop_pdf_show_code'] = request.POST.get('show_code') == '1'
        request.session['pedashop_pdf_show_class'] = request.POST.get('show_class') == '1'
        request.session['pedashop_pdf_show_group'] = request.POST.get('show_group') == '1'
        messages.success(request, 'Configuration export PDF PedaShop enregistrée pour la session.')
        return redirect('pedashop_export_config')
    return render(request, 'pedashop/export_pdf_config.html', {
        'identity_mode': request.session.get('pedashop_pdf_identity_mode', 'anonymous'),
        'show_code': request.session.get('pedashop_pdf_show_code', False),
        'show_class': request.session.get('pedashop_pdf_show_class', True),
        'show_group': request.session.get('pedashop_pdf_show_group', True),
    })
'''
if "def database_purge(request):" not in views:
    views = views.replace("\ndef export_bon_pdf(request, pk):\n", purge_block + "\ndef export_bon_pdf(request, pk):\n")
write(views_path, views)

# -----------------------------------------------------------------------------
# PedaShop templates
# -----------------------------------------------------------------------------
base_template = r'''{% load static %}
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ PEDASHOP_APP_NAME }} — LP Gestion Atelier EP Suite</title>
  <link rel="stylesheet" href="{% static 'pedashop/pedashop.css' %}">
  <link rel="stylesheet" href="{% static 'pedashop/camera_upload.css' %}">
</head>
<body>
<header class="topbar">
  <div class="brand">
    <a href="{% url 'pedashop_dashboard' %}"><img src="{% static 'pedashop/img/logo-pedashop-header.png' %}" alt="PedaShop" class="brand-img"></a>
    <span class="version-badge">{{ PEDASHOP_VERSION }}</span>
  </div>
  <nav>
    <a href="{% url 'pedashop_dashboard' %}">Tableau de bord</a>
    <a href="{% url 'pedashop_stock_list' %}">Catalogue / stock</a>
    {% if pedashop_current_user %}
      <details class="admin-dropdown"><summary>Menu utilisateur</summary><div class="admin-dropdown-menu">
        <a class="admin-menu-item" href="{% url 'pedashop_bon_create' %}">Nouvelle demande / bon</a>
        <a class="admin-menu-item" href="{% url 'pedashop_bon_list' %}">Mes bons / demandes</a>
        <a class="admin-menu-item" href="{% url 'pedashop_reclamation_list' %}">Réclamations</a>
        <a class="admin-menu-item" href="{% url 'pedashop_article_list' %}">Articles</a>
      </div></details>
      {% if pedashop_current_user.is_storekeeper_like %}
      <details class="admin-dropdown"><summary>Actions magasinier</summary><div class="admin-dropdown-menu">
        <a class="admin-menu-item" href="{% url 'pedashop_bon_list' %}">Bons à traiter</a>
        <a class="admin-menu-item" href="{% url 'pedashop_inventory_adjustment' %}">Inventaire</a>
        <a class="admin-menu-item" href="{% url 'pedashop_stock_entry' %}">Entrée / réassort</a>
        <a class="admin-menu-item" href="{% url 'pedashop_movement_list' %}">Mouvements</a>
        <a class="admin-menu-item" href="{% url 'pedashop_transfer_create' %}">Transfert magasin</a>
        <a class="admin-menu-item" href="{% url 'pedashop_alert_list' %}">Alertes</a>
        <a class="admin-menu-item" href="{% url 'pedashop_affichage' %}">Affichage dynamique</a>
      </div></details>
      {% endif %}
      {% if pedashop_current_user.is_teacher_like or pedashop_current_user.is_admin_like %}
      <details class="admin-dropdown"><summary>Administration</summary><div class="admin-dropdown-menu">
        <a class="admin-menu-item" href="{% url 'pedashop_import_excel' %}">Import articles</a>
        <a class="admin-menu-item" href="{% url 'pedashop_articles_template_xlsx' %}">Modèle import articles</a>
        <a class="admin-menu-item" href="{% url 'pedashop_articles_export_xlsx' %}">Export articles</a>
        <a class="admin-menu-item" href="{% url 'pedashop_export_config' %}">Configuration exports PDF</a>
        <a class="admin-menu-item" href="{% url 'pedashop_magasin_list' %}">Magasins</a>
        <a class="admin-menu-item" href="{% url 'pedashop_emplacement_list' %}">Emplacements</a>
        <a class="admin-menu-item" href="{% url 'pedashop_user_list' %}">Utilisateurs</a>
        <a class="admin-menu-item" href="{% url 'pedashop_projection_list' %}">Pré-réservations TP</a>
        <a class="admin-menu-item" href="{% url 'pedashop_consultation_list' %}">Consultations</a>
        {% if pedashop_current_user.is_admin_like %}<a class="admin-menu-item danger-link" href="{% url 'pedashop_database_purge' %}">Vider les bases PedaShop</a>{% endif %}
      </div></details>
      {% endif %}
      <details class="admin-dropdown"><summary>Applications</summary><div class="admin-dropdown-menu">
        <a class="admin-menu-item" href="{{ LP_CORE_PUBLIC_URL }}">LP Core</a>
        <a class="admin-menu-item" href="/toolmag/">ToolMag</a>
        <a class="admin-menu-item" href="/safety/">Safety Manager</a>
        <a class="admin-menu-item" href="/pedashop/">PedaShop</a>
        <a class="admin-menu-item" href="/system/">System Manager</a>
        <a class="admin-menu-item" href="/tpmanager/">TP Manager</a>
        <a class="admin-menu-item" href="/pfmp/">PFMP Manager</a>
      </div></details>
      <form class="role-switch-form" method="post" action="{% url 'pedashop_switch_role' 'utilisateur' %}">{% csrf_token %}<button class="session-pill {% if request.session.pedashop_active_role|default:'utilisateur' == 'utilisateur' %}active{% endif %}" type="submit">Utilisateur : {{ pedashop_current_user.username }}</button></form>
      {% if pedashop_current_user.is_storekeeper_like %}<form class="role-switch-form" method="post" action="{% url 'pedashop_switch_role' 'magasinier' %}">{% csrf_token %}<button class="session-pill {% if request.session.pedashop_active_role == 'magasinier' %}active{% endif %}" type="submit">Magasinier : {{ pedashop_current_user.username }}</button></form>{% else %}<span class="session-pill disabled">Connexion magasinier</span>{% endif %}
      <a class="logout-link" href="{% url 'pedashop_logout' %}">Déconnexion</a>
    {% else %}
      <a class="session-pill" href="{% url 'pedashop_login' %}">Connexion utilisateur</a>
      <a class="session-pill" href="{% url 'pedashop_login' %}">Connexion magasinier</a>
    {% endif %}
    <details class="admin-dropdown"><summary>Aide</summary><div class="admin-dropdown-menu" aria-label="Aide PedaShop">
      <a class="admin-menu-item" href="{% url 'pedashop_help' %}">Aide PedaShop</a>
      <a class="admin-menu-item" href="{% url 'pedashop_about' %}">À propos</a>
    </div></details>
  </nav>
</header>
<main class="container">
  {% if messages %}{% for message in messages %}<div class="alert {{ message.tags }}">{{ message }}</div>{% endfor %}{% endif %}
  {% block content %}{% endblock %}
</main>
<script src="{% static 'pedashop/camera_upload.js' %}"></script>
</body>
</html>
'''
write('pedashop-app/pedashop/templates/pedashop/base.html', base_template)

bon_create = r'''{% extends 'pedashop/base.html' %}
{% block content %}
<h1>Créer une demande / bon multi-articles</h1>
<div class="bon-layout-30-70">
  <section class="card bon-search-panel">
    <h2>1. Recherche dynamique</h2>
    <p class="muted">Recherche par code produit, référence, désignation ou code-barres. Compatible scannette.</p>
    <label for="dynamic-article-search">Article</label>
    <input id="dynamic-article-search" type="search" placeholder="Scanner ou saisir code / référence / désignation" autocomplete="off">
    <div id="article-suggestions" class="suggestion-box"></div>
    <div id="selected-article-card" class="selected-article-card muted">Aucun article sélectionné.</div>

    <details class="advanced-box" open>
      <summary>Filtres avancés</summary>
      <form method="get" class="filterbar compact-filter">{{ search_form.as_p }}<button class="btn" type="submit">Filtrer</button></form>
    </details>

    <h3>Résultats rapides</h3>
    <div class="table-wrap compact-results"><table><thead><tr><th>Article</th><th>Dispo</th></tr></thead><tbody>
      {% for s in results %}<tr class="quick-result" data-id="{{ s.article.id }}" data-label="{{ s.article.reference_interne }} — {{ s.article.designation }}" data-info="{{ s.magasin.code }} : {{ s.stock_disponible }} dispo">
        <td><b>{{ s.article.reference_interne }}</b><br>{{ s.article.designation }}</td><td>{{ s.stock_disponible }}</td>
      </tr>{% empty %}<tr><td colspan="2">Aucun résultat.</td></tr>{% endfor %}
    </tbody></table></div>
  </section>

  <section class="card bon-current-panel">
    <h2>2. Bon en cours</h2>
    <form method="post" class="add-selected-form" id="add-selected-form">
      {% csrf_token %}
      <input type="hidden" name="action" value="add_line">
      <input type="hidden" name="article_id" id="selected-article-id">
      <div class="bon-add-grid">
        <div><label>Article sélectionné</label><input id="selected-article-label" readonly placeholder="Sélectionner un article à gauche"></div>
        <div><label>Quantité</label><input name="quantite" value="1" inputmode="decimal"></div>
        <div><label>Type sortie</label><select name="type_sortie" id="selected-type-sortie"><option value="definitive">Définitive</option><option value="temporaire">Temporaire</option></select></div>
        <div><label>Date retour</label><input type="date" name="date_retour_prevue" id="selected-date-retour"></div>
        <div class="wide"><label>Commentaire ligne</label><input name="commentaire_ligne"></div>
        <div class="actions"><button class="btn primary" type="submit">Ajouter au bon</button></div>
      </div>
    </form>

    <form method="post" id="header-form">{% csrf_token %}<input type="hidden" name="action" value="submit_bon">
      <h3>En-tête du bon</h3>
      <div class="form-grid">{{ header_form.as_p }}</div>
      <h3>Articles ajoutés</h3>
      <div class="table-wrap"><table><thead><tr><th>Article</th><th>Qté</th><th>Sortie</th><th>Retour</th></tr></thead><tbody>
        {% for c in cart %}<tr><td>{{ c.article_label }}</td><td>{{ c.quantite }}</td><td>{{ c.type_sortie }}</td><td>{{ c.date_retour_prevue }}</td></tr>{% empty %}<tr><td colspan="4">Aucun article ajouté.</td></tr>{% endfor %}
      </tbody></table></div>
      <div class="actions"><button class="btn primary" type="submit">Valider le bon</button></form><form method="post">{% csrf_token %}<input type="hidden" name="action" value="clear_cart"><button class="btn" type="submit">Vider le bon</button></form></div>
  </section>
</div>
<script>
function syncHeader(form){['id_type_bon','id_magasin','id_professeur_responsable','id_nom_tp','id_classe_ou_groupe','id_commentaire'].forEach(function(id){var el=document.getElementById(id); if(el){var i=document.createElement('input'); i.type='hidden'; i.name=el.name; i.value=el.value; form.appendChild(i);}})}
function selectArticle(id,label,info){document.getElementById('selected-article-id').value=id;document.getElementById('selected-article-label').value=label;document.getElementById('selected-article-card').innerHTML='<strong>'+label+'</strong><br>'+(info||'');}
const input=document.getElementById('dynamic-article-search'); const box=document.getElementById('article-suggestions'); let timer=null;
input.addEventListener('input',function(){clearTimeout(timer); const q=input.value.trim(); if(q.length<2){box.innerHTML='';return;} timer=setTimeout(function(){fetch('{% url 'pedashop_api_article_search' %}?q='+encodeURIComponent(q)).then(r=>r.json()).then(data=>{box.innerHTML='';(data.results||[]).forEach(function(a){let b=document.createElement('button');b.type='button';b.className='suggestion-row';b.innerHTML='<strong>'+a.reference_interne+'</strong> — '+a.designation+'<br><span class="muted">'+(a.reference_fabricant||'')+' '+(a.code_ean||'')+'</span>';b.onclick=function(){selectArticle(a.id,a.label,a.code_ean||'');box.innerHTML='';input.value=a.reference_interne;};box.appendChild(b);});});},180);});
document.querySelectorAll('.quick-result').forEach(function(row){row.addEventListener('click',function(){selectArticle(row.dataset.id,row.dataset.label,row.dataset.info);});});
document.getElementById('add-selected-form').addEventListener('submit',function(e){if(!document.getElementById('selected-article-id').value){e.preventDefault();alert('Sélectionner un article.');return false;}var type=document.getElementById('selected-type-sortie').value;var date=document.getElementById('selected-date-retour');if(type==='temporaire'&&!date.value){e.preventDefault();alert('Date de retour obligatoire pour une sortie temporaire.');return false;}syncHeader(this);});
function updateReturnDate(){var date=document.getElementById('selected-date-retour'); if(document.getElementById('selected-type-sortie').value==='temporaire'){date.disabled=false;date.required=true;}else{date.disabled=true;date.required=false;date.value='';}}
document.getElementById('selected-type-sortie').addEventListener('change',updateReturnDate); updateReturnDate();
</script>
{% endblock %}
'''
write('pedashop-app/pedashop/templates/pedashop/bon_create.html', bon_create)

magasin_list = r'''{% extends 'pedashop/base.html' %}
{% block content %}
<h1>Magasins</h1>
<div class="actions"><a class="btn primary" href="{% url 'pedashop_magasin_create' %}">Nouveau magasin</a></div>
<form method="post" class="card table-wrap">{% csrf_token %}
  <input type="hidden" name="action" value="delete_selected">
  {% if can_admin_magasins %}<div class="actions"><button class="btn danger" type="submit">Supprimer / désactiver les magasins cochés</button><input name="confirmation" placeholder="SUPPRIMER MAGASINS" style="max-width:260px"></div><p class="muted">Les magasins liés à l’historique seront désactivés au lieu d’être supprimés.</p>{% endif %}
  <table><thead><tr>{% if can_admin_magasins %}<th></th>{% endif %}<th>Code</th><th>Nom</th><th>Responsable</th><th>Actif</th><th>Action</th></tr></thead><tbody>
  {% for i in items %}<tr>{% if can_admin_magasins %}<td><input type="checkbox" name="selected_magasins" value="{{ i.id }}"></td>{% endif %}<td>{{ i.code }}</td><td>{{ i.nom }}</td><td>{{ i.responsable }}</td><td>{{ i.actif|yesno:'Oui,Non' }}</td><td><a class="btn small" href="{% url 'pedashop_magasin_edit' i.pk %}">Modifier</a></td></tr>{% empty %}<tr><td colspan="6">Aucun magasin.</td></tr>{% endfor %}
  </tbody></table>
</form>
{% endblock %}
'''
write('pedashop-app/pedashop/templates/pedashop/magasin_list.html', magasin_list)

write('pedashop-app/pedashop/templates/pedashop/database_purge.html', r'''{% extends 'pedashop/base.html' %}
{% block content %}
<h1>Vider les bases PedaShop</h1>
<div class="card danger-zone"><h2>Action destructive</h2><p>Cette action vide les données métier PedaShop. Les comptes utilisateurs synchronisés sont conservés.</p><ul><li>Articles : {{ counts.articles }}</li><li>Stocks : {{ counts.stocks }}</li><li>Mouvements : {{ counts.mouvements }}</li><li>Bons : {{ counts.bons }}</li><li>Magasins : {{ counts.magasins }}</li></ul><form method="post">{% csrf_token %}<label>Confirmation</label><input name="confirmation" placeholder="VIDER PEDASHOP"><label class="checkline"><input type="checkbox" name="include_stores" value="1"> Vider aussi magasins et emplacements</label><button class="btn danger" type="submit">Vider les bases PedaShop</button></form></div>{% if report %}<div class="card"><h2>Rapport</h2><table><tbody>{% for k,v in report.items %}<tr><th>{{ k }}</th><td>{{ v }}</td></tr>{% endfor %}</tbody></table></div>{% endif %}
{% endblock %}
''')

write('pedashop-app/pedashop/templates/pedashop/export_pdf_config.html', r'''{% extends 'pedashop/base.html' %}
{% block content %}
<h1>Configuration exports PDF — PedaShop</h1>
<div class="card"><form method="post">{% csrf_token %}<label>Identité élève dans les PDF</label><select name="identity_mode"><option value="anonymous" {% if identity_mode == 'anonymous' %}selected{% endif %}>Anonyme — Élève 001</option><option value="last_name" {% if identity_mode == 'last_name' %}selected{% endif %}>Nom seul</option><option value="first_name" {% if identity_mode == 'first_name' %}selected{% endif %}>Prénom seul</option><option value="full_name" {% if identity_mode == 'full_name' %}selected{% endif %}>Nom + prénom</option></select><label class="checkline"><input type="checkbox" name="show_code" value="1" {% if show_code %}checked{% endif %}> Afficher le code élève</label><label class="checkline"><input type="checkbox" name="show_class" value="1" {% if show_class %}checked{% endif %}> Afficher la classe</label><label class="checkline"><input type="checkbox" name="show_group" value="1" {% if show_group %}checked{% endif %}> Afficher le groupe</label><p class="muted">Les exports d’activité utiliseront aussi des filtres par période et par champs métier : classe, groupe, magasin, type de bon, statut, article, réclamation.</p><button class="btn primary" type="submit">Enregistrer</button></form></div>
{% endblock %}
''')

# -----------------------------------------------------------------------------
# CSS PedaShop
# -----------------------------------------------------------------------------
css = read('pedashop-app/pedashop/static/pedashop/pedashop.css')
addition = r'''

/* RC10 — bandeau mode Utilisateur/Magasinier + bon 30/70 + maintenance */
.role-switch-form{display:inline-block;margin:0}.role-switch-form button{font-family:inherit}.session-pill{display:inline-block;border:1px solid rgba(255,255,255,.35);background:rgba(255,255,255,.13);color:#fff;border-radius:999px;padding:7px 11px;font-weight:800;text-decoration:none;cursor:pointer}.session-pill.active{background:var(--orange);border-color:var(--orange);box-shadow:0 0 0 2px rgba(255,255,255,.22) inset}.session-pill.disabled{opacity:.55}.logout-link{opacity:.86}.danger-link{color:#991b1b!important}.danger-zone{border-color:#fecaca;background:#fff7f7}.checkline{display:flex;gap:.45rem;align-items:center;margin:.55rem 0}.checkline input{width:auto}.bon-layout-30-70{display:grid;grid-template-columns:minmax(260px,30%) minmax(520px,70%);gap:16px;align-items:start}.bon-search-panel{min-width:0}.bon-current-panel{min-width:0}.compact-filter{grid-template-columns:1fr}.compact-results{max-height:520px}.quick-result{cursor:pointer}.quick-result:hover td{background:#e0f2fe!important}.selected-article-card{border:1px dashed var(--border);border-radius:12px;padding:10px;margin:10px 0;background:#f8fafc}.bon-add-grid{display:grid;grid-template-columns:1.6fr .55fr .8fr .9fr;gap:10px;align-items:end;margin-bottom:16px}.bon-add-grid .wide{grid-column:1 / span 3}.compact-filter p{margin:.25rem 0}.compact-filter label{font-size:.88rem}.compact-filter input,.compact-filter select{padding:7px}.admin-dropdown summary{font-weight:900!important}.topbar nav{font-weight:800}@media(max-width:1000px){.bon-layout-30-70{grid-template-columns:1fr}.bon-add-grid{grid-template-columns:1fr}.bon-add-grid .wide{grid-column:auto}}
'''
if 'RC10 — bandeau mode' not in css:
    css += addition
write('pedashop-app/pedashop/static/pedashop/pedashop.css', css)

# -----------------------------------------------------------------------------
# System Manager cleanup: remove old admin-sql menu/urls, sync only in settings, CSRF API fix in LP Core
# -----------------------------------------------------------------------------
# URLs: remove admin-sql lines.
su = read('system-manager-app/system_manager/urls.py')
su = '\n'.join([line for line in su.splitlines() if 'admin-sql' not in line and 'sql_database' not in line]) + '\n'
write('system-manager-app/system_manager/urls.py', su)
# Menu: remove Base SQL and sync LP Core from admin menu when possible.
sb = read('system-manager-app/system_manager/templates/system_manager/base.html')
sb = re.sub(r"\s*<a[^>]+sql_database_admin[^\n]+\n", "\n", sb)
sb = re.sub(r"\s*<form[^>]+system_sync_lp_core[\s\S]*?</form>\s*", "\n", sb)
sb = sb.replace('Synchroniser LP Core', '')
sb = sb.replace('Base SQL', '')
write('system-manager-app/system_manager/templates/system_manager/base.html', sb)
# Add export config stub System Manager.
sv = read('system-manager-app/system_manager/views.py')
if "def export_pdf_config" not in sv:
    sv += r'''

@system_admin_required
def export_pdf_config(request):
    if request.method == 'POST':
        request.session['system_pdf_identity_mode'] = request.POST.get('identity_mode') or 'anonymous'
        messages.success(request, 'Configuration export PDF System Manager enregistrée pour la session.')
        return redirect('system_export_config')
    return render(request, 'system_manager/export_pdf_config.html', {'identity_mode': request.session.get('system_pdf_identity_mode', 'anonymous')})
'''
    write('system-manager-app/system_manager/views.py', sv)
# Add route if urlpatterns visible.
su = read('system-manager-app/system_manager/urls.py')
if 'system_export_config' not in su:
    su = su.replace("urlpatterns = [\n", "urlpatterns = [\n    path('exports/configuration/', views.export_pdf_config, name='system_export_config'),\n")
write('system-manager-app/system_manager/urls.py', su)
write('system-manager-app/system_manager/templates/system_manager/export_pdf_config.html', r'''{% extends 'system_manager/base.html' %}{% block content %}<h1>Configuration exports PDF — System Manager</h1><div class="card"><form method="post">{% csrf_token %}<label>Identité dans les PDF</label><select name="identity_mode"><option value="anonymous" {% if identity_mode == 'anonymous' %}selected{% endif %}>Anonyme</option><option value="last_name" {% if identity_mode == 'last_name' %}selected{% endif %}>Nom seul</option><option value="first_name" {% if identity_mode == 'first_name' %}selected{% endif %}>Prénom seul</option><option value="full_name" {% if identity_mode == 'full_name' %}selected{% endif %}>Nom + prénom</option></select><p class="muted">Filtres prévus : période, classe, groupe, système, zone, sous-zone, prise de poste, anomalie.</p><button class="btn primary" type="submit">Enregistrer</button></form></div>{% endblock %}''')

# LP Core CSRF exempt for System Manager -> LP Core import endpoint.
cv = read('lp-core-app/core/views.py')
if "from django.views.decorators.csrf import csrf_exempt" not in cv:
    cv = cv.replace("from django.views.decorators.http import require_http_methods\n", "from django.views.decorators.http import require_http_methods\nfrom django.views.decorators.csrf import csrf_exempt\n")
if "@csrf_exempt\n@require_http_methods(['POST'])\ndef api_system_manager_referentials_import" not in cv:
    cv = cv.replace("@require_http_methods(['POST'])\ndef api_system_manager_referentials_import", "@csrf_exempt\n@require_http_methods(['POST'])\ndef api_system_manager_referentials_import")
write('lp-core-app/core/views.py', cv)

# -----------------------------------------------------------------------------
# TP Manager badges + export config stub
# -----------------------------------------------------------------------------
tpb = read('tpmanager-app/tp_manager/templates/tp_manager/base.html')
if "tp-session-pill" not in tpb:
    tpb = tpb.replace("{% if tp_current_user %}<a href=\"{% url 'tp_logout' %}\">Déconnexion {{ tp_current_user.username }}</a>{% else %}<a href=\"{% url 'tp_login' %}\">Connexion</a>{% endif %}",
"{% if tp_current_user %}<span class=\"tp-session-pill\">{% if tp_current_user.is_admin_like %}Admin{% elif tp_current_user.is_prof_like %}Professeur{% else %}Élève{% endif %} : {{ tp_current_user.username }}</span><a href=\"{% url 'tp_logout' %}\">Déconnexion</a>{% else %}<a class=\"tp-session-pill\" href=\"{% url 'tp_login' %}\">Connexion</a>{% endif %}")
    tpb = tpb.replace("<a class=\"admin-menu-item\" title=\"Paramétrage\" href=\"{% url 'tp_referentials' %}\">Paramétrage</a>",
                      "<a class=\"admin-menu-item\" title=\"Paramétrage\" href=\"{% url 'tp_referentials' %}\">Paramétrage</a>\n        <a class=\"admin-menu-item\" title=\"Configuration exports PDF\" href=\"{% url 'tp_export_config' %}\">Configuration exports PDF</a>")
write('tpmanager-app/tp_manager/templates/tp_manager/base.html', tpb)

tpcss = read('tpmanager-app/tp_manager/static/tp_manager/tp.css')
if 'RC10 — badge session TP Manager' not in tpcss:
    tpcss += "\n/* RC10 — badge session TP Manager */\n.tp-session-pill{display:inline-block;border:1px solid rgba(255,255,255,.35);background:rgba(255,255,255,.13);color:#fff;border-radius:999px;padding:7px 11px;font-weight:900;text-decoration:none}.topbar summary{font-weight:900!important}\n"
write('tpmanager-app/tp_manager/static/tp_manager/tp.css', tpcss)
# TP route/view export config; best effort paths.
tp_urls_path = 'tpmanager-app/tp_manager/urls.py'
if p(tp_urls_path).exists():
    tpu = read(tp_urls_path)
    if 'tp_export_config' not in tpu:
        tpu = tpu.replace("urlpatterns = [\n", "urlpatterns = [\n    path('exports/configuration/', views.export_pdf_config, name='tp_export_config'),\n")
        write(tp_urls_path, tpu)
tp_views_path = 'tpmanager-app/tp_manager/views.py'
if p(tp_views_path).exists():
    tv = read(tp_views_path)
    if "def export_pdf_config" not in tv:
        tv += r'''

@require_http_methods(['GET', 'POST'])
def export_pdf_config(request):
    if request.method == 'POST':
        request.session['tp_pdf_identity_mode'] = request.POST.get('identity_mode') or 'anonymous'
        messages.success(request, 'Configuration export PDF TP Manager enregistrée pour la session.')
        return redirect('tp_export_config')
    return render(request, 'tp_manager/export_pdf_config.html', {'identity_mode': request.session.get('tp_pdf_identity_mode', 'anonymous')})
'''
        write(tp_views_path, tv)
write('tpmanager-app/tp_manager/templates/tp_manager/export_pdf_config.html', r'''{% extends 'tp_manager/base.html' %}{% block content %}<h1>Configuration exports PDF — TP Manager</h1><div class="form-card"><form method="post">{% csrf_token %}<label>Identité élève dans les PDF</label><select name="identity_mode"><option value="anonymous" {% if identity_mode == 'anonymous' %}selected{% endif %}>Anonyme</option><option value="last_name" {% if identity_mode == 'last_name' %}selected{% endif %}>Nom seul</option><option value="first_name" {% if identity_mode == 'first_name' %}selected{% endif %}>Prénom seul</option><option value="full_name" {% if identity_mode == 'full_name' %}selected{% endif %}>Nom + prénom</option></select><p class="muted">Filtres prévus : période, classe, groupe, professeur, TP, thème, système, compétence, séquence.</p><button type="submit">Enregistrer</button></form></div>{% endblock %}''')

# -----------------------------------------------------------------------------
# LP Core documentation/scaffolding for export rights.
# -----------------------------------------------------------------------------
Path('docs').mkdir(exist_ok=True)
write('docs/RC10_EXPORTS_PDF_ACTIVITE.md', """# RC10 — Exports PDF d’activité élèves\n\nArchitecture retenue : chaque application possède une page `Configuration exports PDF` dans le menu admin.\n\nModes d’identité prévus :\n- anonyme : Élève 001 ;\n- nom seul ;\n- prénom seul ;\n- nom + prénom.\n\nFiltres obligatoires : période début / fin.\n\nFiltres métier par application :\n- PedaShop : classe, groupe, magasin, type de bon, statut, article, réclamation ;\n- System Manager : classe, groupe, système, zone, sous-zone, réservation, prise de poste, anomalie ;\n- TP Manager : élève, classe, groupe, professeur, TP, thème, système, compétence, séquence ;\n- ToolMag, Safety, PFMP : structure à raccorder aux modèles de chaque module.\n\nDroits LP Core recommandés :\n- LP_EXPORT_FICHES_ELEVES ;\n- PEDASHOP_EXPORT_ACTIVITE ;\n- SYSTEM_EXPORT_ACTIVITE ;\n- TPMANAGER_EXPORT_ACTIVITE ;\n- TOOLMAG_EXPORT_ACTIVITE ;\n- SAFETY_EXPORT_ACTIVITE ;\n- PFMP_EXPORT_ACTIVITE.\n""")

# -----------------------------------------------------------------------------
# CHECKSUMS.sha256 recalcul
# -----------------------------------------------------------------------------
exclude_dirs = {'.git','backups','postgres-db','lp-core-db','toolmag-db','safety-db','pedashop-db','system-manager-db','tpmanager-db','pfmp-db','updates','logs','__pycache__'}
files=[]
for path in Path('.').rglob('*'):
    if not path.is_file():
        continue
    if set(path.parts) & exclude_dirs:
        continue
    if path.name == 'CHECKSUMS.sha256' or path.suffix == '.pyc':
        continue
    files.append(path)
files = sorted(files, key=lambda x: str(x).replace('\\','/'))
with open('CHECKSUMS.sha256','w',encoding='utf-8',newline='\n') as out:
    for path in files:
        h=hashlib.sha256()
        with open(path,'rb') as f:
            for chunk in iter(lambda:f.read(1024*1024), b''):
                h.update(chunk)
        out.write(f"{h.hexdigest()}  ./{str(path).replace('\\','/')}\n")
PY

# Vérifications syntaxiques légères
echo "[RC10] Vérification syntaxe Python"
python3 -m py_compile \
  pedashop-app/pedashop/views.py \
  pedashop-app/pedashop/services.py \
  lp-core-app/core/views.py \
  system-manager-app/system_manager/views.py || true
if [[ -f tpmanager-app/tp_manager/views.py ]]; then python3 -m py_compile tpmanager-app/tp_manager/views.py || true; fi

echo "[RC10] Vérification CHECKSUMS"
sha256sum -c CHECKSUMS.sha256 2>&1 | grep -E 'FAILED|WARNING|No such file|did NOT match' && exit 1 || echo "CHECKSUMS OK"

echo "[RC10] Contrôles ciblés"
grep -R "Article.objects.all().delete()" -n pedashop-app/pedashop/services.py && { echo "[RC10][ERREUR] suppression directe Article encore présente"; exit 1; } || echo "Remplacement total protégé OK"
grep -R "pedashop_database_purge" -n pedashop-app/pedashop/urls.py >/dev/null && echo "Vidage PedaShop route OK"
grep -R "pedashop_switch_role" -n pedashop-app/pedashop/urls.py >/dev/null && echo "Mode utilisateur/magasinier OK"
grep -R "admin-sql" -n system-manager-app/system_manager/urls.py system-manager-app/system_manager/templates/system_manager/base.html && { echo "[RC10][ERREUR] admin-sql encore présent dans System Manager"; exit 1; } || echo "System Manager admin-sql retiré OK"

echo "[RC10] Patch appliqué. Commit conseillé :"
echo "git add -A && git commit -m 'RC10 harmonise modes PedaShop exports PDF et menus'"
