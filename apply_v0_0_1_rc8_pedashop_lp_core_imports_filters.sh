#!/usr/bin/env bash
set -euo pipefail

echo "[RC8] Application : PedaShop imports/filtres + LP Core modèles/recherche/magasins modules"
ROOT="$(pwd)"
if [[ ! -f "docker-compose.yml" ]]; then
  echo "Erreur : lance ce script depuis la racine du dépôt LP Suite."
  exit 1
fi

python3 <<'PY'
from pathlib import Path
import re, json, textwrap

ROOT = Path('.')
VERSION = 'V0.0.1-RC8'

def p(path): return ROOT / path

def read(path):
    return p(path).read_text(encoding='utf-8')

def write(path, text):
    p(path).parent.mkdir(parents=True, exist_ok=True)
    p(path).write_text(text.rstrip() + '\n', encoding='utf-8')

def replace_regex(path, pattern, repl, flags=re.S):
    text = read(path)
    new, n = re.subn(pattern, repl, text, flags=flags)
    if n == 0:
        raise SystemExit(f'[RC8] Motif introuvable dans {path}: {pattern[:120]}')
    write(path, new)

# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------
for vf in ['VERSION', 'VERSION.txt', '.suite-target-version']:
    if p(vf).exists():
        write(vf, VERSION)

if p('manifest.json').exists():
    try:
        data = json.loads(read('manifest.json'))
        for key in ['version', 'suite_version', 'target_version']:
            if key in data:
                data[key] = VERSION
        write('manifest.json', json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        text = read('manifest.json')
        text = re.sub(r'V0\.0\.1-RC\d+', VERSION, text)
        write('manifest.json', text)

# ---------------------------------------------------------------------------
# LP Core : modèle Excel utilisateurs téléchargeable
# ---------------------------------------------------------------------------
core_views = p('lp-core-app/core/views.py')
if core_views.exists():
    txt = core_views.read_text(encoding='utf-8')
    if 'def users_import_template_xlsx' not in txt:
        func = r'''


def users_import_template_xlsx(request):
    """Modèle Excel officiel pour éviter les erreurs d'import élèves/utilisateurs."""
    if not require_core_admin(request):
        return redirect('core_login')
    from openpyxl import Workbook
    from io import BytesIO
    wb = Workbook()
    ws = wb.active
    ws.title = 'Utilisateurs LP Core'
    headers = [
        'code', 'identifiant', 'mot_de_passe_initial', 'nom', 'prenom', 'email',
        'classe', 'formation', 'groupe', 'role', 'droits', 'actif', 'annee_scolaire'
    ]
    ws.append(headers)
    ws.append([
        'PROF-0001', 'prof-0001', 'prof1234', 'DUPONT', 'Alice',
        'alice.dupont@example.fr', '1MELEC', 'MELEC', 'Groupe A',
        'professeur', 'PEDASHOP_PROF;TOOLMAG_PROF', '1', '2026-2027'
    ])
    ws.append([
        'ELE-0001', 'ele-0001', 'ele1234', 'MARTIN', 'Noa',
        '', '2MTNE1', 'MTNE', 'Groupe B',
        'eleve', '', '1', '2026-2027'
    ])
    for col in ws.columns:
        max_len = max(len(str(c.value or '')) for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(max_len + 4, 14), 34)
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="modele_import_eleves_lp_core.xlsx"'
    return response
'''
        marker = "def _module_sync_timeout():"
        if marker in txt:
            txt = txt.replace(marker, func + "\n\n" + marker)
        else:
            txt += func
    # Magasins LP Core → modules : global + module spécifique pour PedaShop
    txt = txt.replace("store__module='pedashop'", "store__module__in=['global', 'pedashop']")
    core_views.write_text(txt, encoding='utf-8')

core_urls = p('lp-core-app/lp_core_project/urls.py')
if core_urls.exists():
    txt = core_urls.read_text(encoding='utf-8')
    if "core_users_import_template" not in txt:
        txt = txt.replace(
            "path('utilisateurs/import/', views.users_import, name='core_users_import'),",
            "path('utilisateurs/import/', views.users_import, name='core_users_import'),\n    path('utilisateurs/import/modele.xlsx', views.users_import_template_xlsx, name='core_users_import_template'),"
        )
    core_urls.write_text(txt, encoding='utf-8')

write('lp-core-app/core/templates/core/users_import.html', r'''
{% extends 'core/base.html' %}
{% block content %}
<h1>Import Excel élèves / utilisateurs</h1>
<section class="panel">
  <h2>Modèle officiel</h2>
  <p>Utilise le modèle téléchargeable pour éviter les erreurs de colonnes. Les colonnes peuvent rester vides sauf <code>nom</code> et <code>prenom</code>.</p>
  <p><a class="button primary" href="{% url 'core_users_import_template' %}">Télécharger le modèle Excel élèves / utilisateurs</a></p>
  <div class="alert info">
    Colonnes reconnues : <code>code</code>, <code>identifiant</code>, <code>mot_de_passe_initial</code>, <code>nom</code>, <code>prenom</code>, <code>email</code>, <code>classe</code>, <code>formation</code>, <code>groupe</code>, <code>role</code>, <code>droits</code>, <code>actif</code>, <code>annee_scolaire</code>.
  </div>
</section>
<section class="panel">
  <h2>Importer</h2>
  <form method="post" enctype="multipart/form-data" class="form-card">{% csrf_token %}
    <label>Fichier Excel .xlsx<input type="file" name="file" accept=".xlsx" required></label>
    <button type="submit">Importer dans LP Core</button>
  </form>
</section>
{% if report %}
<section class="panel"><h2>Rapport</h2><p>{{ report.created }} créés, {{ report.updated }} mis à jour.</p>{% if report.errors %}<ul class="errors">{% for e in report.errors %}<li>{{ e }}</li>{% endfor %}</ul>{% endif %}</section>
<section class="panel"><h2>Synchronisation modules</h2><p>Après import dans LP Core, pousser la base élèves vers les modules.</p><form method="post" action="{% url 'core_sync_toolmag' %}" class="inline-sync-form">{% csrf_token %}<button class="button primary" type="submit">Synchroniser vers ToolMag</button></form> <form method="post" action="{% url 'core_sync_pedashop' %}" class="inline-sync-form">{% csrf_token %}<button class="button secondary" type="submit">Synchroniser vers PedaShop</button></form></section>
{% endif %}
{% endblock %}
''')

# ---------------------------------------------------------------------------
# LP Core : magasins/droits/certifications avec recherche dynamique et modules
# ---------------------------------------------------------------------------
write('lp-core-app/core/templates/core/stores_list.html', r'''
{% extends 'core/base.html' %}
{% block content %}
<h1>Magasins / droits / certifications</h1>
<p>LP Core porte les droits et les périmètres communs. Les magasins peuvent être affectés à un module précis ou être déclarés <strong>Tous modules</strong>. Les modules synchronisés consomment ensuite ces magasins pour limiter les accès.</p>

<section class="panel">
  <h2>Fonctionnement par module</h2>
  <ul>
    <li><strong>Magasins</strong> : <code>global</code> = visible par tous les modules compatibles ; <code>pedashop</code> = PedaShop seulement ; <code>toolmag</code> = ToolMag seulement.</li>
    <li><strong>Droits</strong> : codes synchronisables vers les modules, par exemple <code>PEDASHOP_PROF</code>, <code>PEDASHOP_MAGASINIER</code>, <code>TOOLMAG_PROF</code>.</li>
    <li><strong>Certifications</strong> : habilitations et autorisations portées par LP Core, consommables par Safety, ToolMag, PedaShop ou System Manager.</li>
    <li><strong>Règles modules</strong> : contrôlent les modules visibles depuis le portail LP Core. Elles ne remplacent pas les droits internes des modules.</li>
  </ul>
</section>

<section class="panel"><h2>Ajouter / mettre à jour un magasin</h2><form method="post" class="form-card">{% csrf_token %}
  <input type="hidden" name="form_action" value="store">
  <label>Module concerné<select name="module">{% for code,label in modules %}<option value="{{ code }}">{{ label }}</option>{% endfor %}</select></label>
  <label>Code magasin<input name="code" placeholder="ATELIER"></label>
  <label>Nom<input name="nom" placeholder="Magasin atelier principal"></label>
  <label>Description<input name="description"></label>
  <label class="checkline"><input type="checkbox" name="active" value="1" checked> Actif</label>
  <button type="submit">Enregistrer</button>
</form></section>

<section class="panel"><h2>Types de droits existants</h2><form method="post" class="form-grid">{% csrf_token %}
  <input type="hidden" name="form_action" value="right">
  <label>Code droit<input name="right_code" placeholder="PEDASHOP_PROF, PEDASHOP_MAGASINIER..."></label>
  <label>Libellé<input name="right_label" placeholder="Professeur PedaShop"></label>
  <label>Module<select name="right_module">{% for code,label in right_modules %}<option value="{{ code }}">{{ label }}</option>{% endfor %}</select></label>
  <label class="checkline"><input type="checkbox" name="right_active" value="1" checked> Actif</label>
  <label class="span-all">Description<input name="right_description"></label>
  <div class="span-all"><button type="submit">Ajouter / mettre à jour le droit</button></div>
</form>
<input class="lp-dyn-filter" data-target="rights-table" placeholder="Filtrer par code, module ou libellé">
<table id="rights-table"><tr><th>Module</th><th>Code</th><th>Libellé</th><th>Actif</th></tr>{% for r in rights %}<tr><td>{{ r.module }}</td><td>{{ r.code }}</td><td>{{ r.label }}</td><td>{{ r.active|yesno:'oui,non' }}</td></tr>{% empty %}<tr><td colspan="4">Aucun droit.</td></tr>{% endfor %}</table></section>

<section class="panel"><h2>Types de certifications / habilitations</h2><form method="post" class="form-grid">{% csrf_token %}
  <input type="hidden" name="form_action" value="cert_type">
  <label>Code<input name="cert_code" placeholder="B1V, BR, SST, FLUIDE_FRIGO..."></label>
  <label>Libellé<input name="cert_label" placeholder="Habilitation B1V"></label>
  <label class="checkline"><input type="checkbox" name="cert_active" value="1" checked> Actif</label>
  <label class="span-all">Description<input name="cert_description"></label>
  <div class="span-all"><button type="submit">Ajouter / mettre à jour le type</button></div>
</form>
<input class="lp-dyn-filter" data-target="cert-table" placeholder="Filtrer par code ou libellé">
<table id="cert-table"><tr><th>Code</th><th>Libellé</th><th>Actif</th></tr>{% for c in cert_types %}<tr><td>{{ c.code }}</td><td>{{ c.label }}</td><td>{{ c.active|yesno:'oui,non' }}</td></tr>{% empty %}<tr><td colspan="3">Aucun type personnalisé.</td></tr>{% endfor %}</table></section>

<section class="panel"><h2>Magasins connus</h2>
<input class="lp-dyn-filter" data-target="stores-table" placeholder="Filtrer par module, code ou désignation">
<table id="stores-table"><tr><th>Module</th><th>Code</th><th>Nom</th><th>Actif</th></tr>{% for s in stores %}<tr><td>{{ s.module }}</td><td>{{ s.code }}</td><td>{{ s.nom }}</td><td>{{ s.active|yesno:'oui,non' }}</td></tr>{% empty %}<tr><td colspan="4">Aucun magasin.</td></tr>{% endfor %}</table></section>

<section class="panel"><h2>Règles de visibilité des modules</h2>
<p>Ces règles pilotent uniquement les modules visibles dans le portail LP Core. Les droits internes des applications restent gérés par chaque module après synchronisation.</p>
<form method="post" class="form-grid">{% csrf_token %}
  <input type="hidden" name="form_action" value="module_rule">
  <label>Module<select name="module_code">{% for code,label in module_choices %}<option value="{{ code }}">{{ label }}</option>{% endfor %}</select></label>
  <label>Cible<select name="target_type">{% for code,label in target_choices %}<option value="{{ code }}">{{ label }}</option>{% endfor %}</select></label>
  <label>Valeur<input name="target_value" placeholder="eleve, 1MELEC, MELEC, groupe A, USR-0001, TOOLMAG_VIEW..."></label>
  <label class="checkline"><input type="checkbox" name="rule_active" value="1" checked> Active</label>
  <label class="span-all">Commentaire<input name="rule_comment" placeholder="Ex. 1MELEC voit System Manager"></label>
  <div class="span-all"><button type="submit">Ajouter / mettre à jour la règle</button></div>
</form>
<input class="lp-dyn-filter" data-target="module-rules-table" placeholder="Filtrer les règles par module, cible ou valeur">
<table id="module-rules-table"><tr><th>Module</th><th>Cible</th><th>Valeur</th><th>Actif</th><th>Commentaire</th><th></th></tr>{% for r in module_rules %}<tr><td>{{ r.get_module_display }}</td><td>{{ r.get_target_type_display }}</td><td>{{ r.target_value }}</td><td>{{ r.active|yesno:'oui,non' }}</td><td>{{ r.comment }}</td><td><form method="post">{% csrf_token %}<input type="hidden" name="form_action" value="delete_module_rule"><input type="hidden" name="rule_id" value="{{ r.id }}"><button class="danger small" type="submit">Supprimer</button></form></td></tr>{% empty %}<tr><td colspan="6">Aucune règle : les valeurs par défaut sont appliquées.</td></tr>{% endfor %}</table></section>

<script>
document.querySelectorAll('.lp-dyn-filter').forEach(input => {
  const table = document.getElementById(input.dataset.target);
  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    table.querySelectorAll('tr').forEach((tr, idx) => {
      if (idx === 0) return;
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
});
</script>
{% endblock %}
''')

write('lp-core-app/core/templates/core/bulk_permissions.html', r'''
{% extends 'core/base.html' %}
{% block content %}
<h1>Gestion par lot — droits, magasins, habilitations et RGPD</h1>
<section class="panel">
  <h2>Fonctionnement</h2>
  <p>Cette page applique une action à tous les utilisateurs cochés, ou à tous les utilisateurs filtrés si aucun utilisateur n'est coché.</p>
  <ul>
    <li><strong>Droits</strong> : ajout ou retrait des codes de droits consommés par les modules.</li>
    <li><strong>Magasins</strong> : affecte les magasins LP Core aux utilisateurs. Les magasins <code>global</code> sont transversaux, les magasins <code>pedashop</code> ou <code>toolmag</code> ciblent un module.</li>
    <li><strong>Certifications</strong> : ajoute une habilitation/certification à tout le lot.</li>
    <li><strong>RGPD</strong> : règle en masse le droit à l'image et les blocages photo/document.</li>
  </ul>
</section>
<form method="get" class="toolbar">
  <input name="q" value="{{ q }}" placeholder="Recherche utilisateur">
  <select name="class_name"><option value="">Toutes classes</option>{% for c in classes %}<option {% if c == class_name %}selected{% endif %}>{{ c }}</option>{% endfor %}</select>
  <select name="formation"><option value="">Toutes formations</option>{% for f in formations %}<option value="{{ f.code }}" {% if f.code == formation %}selected{% endif %}>{{ f.code }}</option>{% endfor %}</select>
  <select name="role"><option value="">Tous rôles</option>{% for code,label in roles %}<option value="{{ code }}" {% if code == role %}selected{% endif %}>{{ label }}</option>{% endfor %}</select>
  <button>Filtrer</button>
</form>
<form method="post">{% csrf_token %}<input type="hidden" name="q" value="{{ q }}"><input type="hidden" name="class_name" value="{{ class_name }}"><input type="hidden" name="formation" value="{{ formation }}"><input type="hidden" name="role" value="{{ role }}">
  <div class="panel"><button type="button" onclick="document.querySelectorAll('.user-check').forEach(c=>c.checked=true)">Tout cocher dans le filtre</button> <button type="button" onclick="document.querySelectorAll('.user-check').forEach(c=>c.checked=false)">Tout décocher</button></div>
  <section class="panel"><h2>Action à appliquer</h2>
    <label>Action<select name="bulk_action" id="bulk-action" onchange="updateBulkBlocks()"><option value="add_right">Ajouter droit</option><option value="remove_right">Retirer droit</option><option value="add_store">Affecter magasin</option><option value="remove_store">Retirer magasin</option><option value="add_certification">Ajouter habilitation / certification</option><option value="set_image_authorization">Droit à l'image / opposition parentale</option></select></label>

    <div class="bulk-block" data-actions="add_right remove_right">
      <h3>Droits</h3>
      <input class="choice-filter" data-target="rights-grid" placeholder="Rechercher droit par code, module ou désignation">
      <div class="rights-grid" id="rights-grid">{% for right in rights_defs %}<label data-filter="{{ right.code }} {{ right.module }} {{ right.label }}"><input type="checkbox" name="rights_codes" value="{{ right.code }}"> <span>{{ right.code }}</span><small>{{ right.module }} — {{ right.label }}</small></label>{% empty %}<p>Aucun droit paramétré.</p>{% endfor %}</div>
    </div>

    <div class="bulk-block" data-actions="add_store remove_store">
      <h3>Magasins</h3>
      <input class="choice-filter" data-target="stores-grid" placeholder="Rechercher magasin par code, module ou désignation">
      <div class="rights-grid" id="stores-grid">{% for s in stores %}<label data-filter="{{ s.code }} {{ s.nom }} {{ s.module }}"><input type="checkbox" name="stores" value="{{ s.pk }}"> <span>{{ s.code }}</span><small>{{ s.nom }} — {{ s.module }}</small></label>{% empty %}<p>Aucun magasin.</p>{% endfor %}</div>
    </div>

    <div class="bulk-block" data-actions="add_certification">
      <h3>Certification / habilitation</h3>
      <div class="form-grid compact">
        <label>Type certification<select name="type_certification">{% for code,label in certification_types %}<option value="{{ code }}">{{ label }}</option>{% endfor %}</select></label>
        <label>Niveau<input name="niveau"></label>
        <label>Date obtention<input name="date_obtention" type="date"></label>
        <label>Date fin validité<input name="date_fin_validite" type="date"></label>
      </div>
    </div>

    <div class="bulk-block" data-actions="set_image_authorization">
      <h3>Droit à l'image / RGPD</h3>
      <div class="form-grid compact">
        <label>Statut<select name="image_consent_status"><option value="unknown">Non renseigné</option><option value="authorized">Autorisation accordée</option><option value="refused">Refus / opposition</option></select></label>
        <label class="checkline"><input type="checkbox" name="parent_image_opposition" value="1"> Opposition parentale mineur</label>
        <label class="checkline"><input type="checkbox" name="personal_upload_blocked" value="1"> Bloquer ajout photo/documents</label>
        <label class="span-all">Commentaire<input name="image_consent_comment" placeholder="Ex. formulaire papier signé / opposition parentale"></label>
      </div>
    </div>

    <button type="submit">Appliquer au lot coché ou filtré</button>
  </section>
  <section class="panel"><h2>Utilisateurs filtrés</h2><table><tr><th></th><th>Code</th><th>Nom</th><th>Classe</th><th>Formation</th><th>Rôle</th><th>Droit image</th><th>Droits</th></tr>{% for u in users %}<tr><td><input class="user-check" type="checkbox" name="selected_users" value="{{ u.pk }}"></td><td>{{ u.code }}</td><td>{{ u.last_name }} {{ u.first_name }}</td><td>{{ u.class_name }}</td><td>{% if u.formation %}{{ u.formation.code }}{% endif %}</td><td>{{ u.role_principal }}</td><td>{{ u.get_image_consent_status_display }}{% if u.parent_image_opposition %}<br><strong>opposition</strong>{% endif %}</td><td>{{ u.rights|truncatechars:45 }}</td></tr>{% empty %}<tr><td colspan="8">Aucun utilisateur.</td></tr>{% endfor %}</table></section>
</form>
<script>
function updateBulkBlocks(){
  const action=document.getElementById('bulk-action').value;
  document.querySelectorAll('.bulk-block').forEach(block=>{
    const allowed=(block.dataset.actions||'').split(' ');
    block.style.display=allowed.includes(action)?'block':'none';
  });
}
updateBulkBlocks();
document.querySelectorAll('.choice-filter').forEach(input=>{
  input.addEventListener('input', ()=>{
    const q=input.value.trim().toLowerCase();
    document.querySelectorAll('#'+input.dataset.target+' label').forEach(label=>{
      label.style.display=(label.dataset.filter||label.textContent).toLowerCase().includes(q)?'':'none';
    });
  });
});
</script>
{% endblock %}
''')

# ---------------------------------------------------------------------------
# PedaShop : formulaires import/stock enrichis
# ---------------------------------------------------------------------------
forms_path = p('pedashop-app/pedashop/forms.py')
if forms_path.exists():
    forms = forms_path.read_text(encoding='utf-8')
    forms = re.sub(r'class ExcelImportForm\(forms\.Form\):.*?\n\nclass TransferForm', r'''class ExcelImportForm(forms.Form):
    MODE_CHOICES = [
        ('append_only', 'Ajout uniquement : ajoute les articles absents et ne modifie pas les existants'),
        ('upsert', 'Mise à jour par clé : modifie si la clé existe, ajoute sinon'),
        ('replace_all', 'Remplacement total : remplace la base articles PedaShop'),
        ('simulation', 'Simulation : analyse sans écrire'),
    ]
    KEY_CHOICES = [
        ('reference_interne', 'Code produit / code interne'),
        ('reference_fabricant', 'Référence fabricant'),
        ('code_ean', 'Code-barres / EAN'),
        ('designation', 'Désignation'),
    ]
    fichier = forms.FileField(label='Fichier Excel .xlsx')
    magasin = forms.ModelChoiceField(queryset=Magasin.objects.filter(actif=True), label='Magasin de destination')
    feuille = forms.CharField(label='Feuille Excel', required=False, help_text='Laisser vide pour prendre la première feuille.')
    mode_import = forms.ChoiceField(choices=MODE_CHOICES, initial='append_only', label='Mode d’import')
    cle_import = forms.ChoiceField(choices=KEY_CHOICES, initial='reference_interne', label='Clé de comparaison')
    ignorer_cellules_vides = forms.BooleanField(required=False, initial=True, label='Ne pas écraser un champ existant par une cellule vide')
    confirmation_remplacement = forms.CharField(required=False, label='Confirmation remplacement total', help_text='Pour le remplacement total, saisir exactement REMPLACER.')
    verifier_coherence_stock = forms.BooleanField(required=False, label='Vérifier la cohérence Qté stock / Qté OK + Usé + HS')

    def __init__(self, *args, allowed_magasins=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_magasins is not None:
            self.fields['magasin'].queryset = allowed_magasins

class TransferForm''', forms, flags=re.S)
    forms = re.sub(r'class StockEntryForm\(forms\.Form\):.*?\n\nclass InventoryAdjustmentForm', r'''class StockEntryForm(forms.Form):
    """Entrée de stock simple : réassort acheté, retour fournisseur ou stock initial."""
    TYPE_CHOICES = [
        ('reception_fournisseur', 'Réassort / réception fournisseur'),
        ('entree_initiale', 'Entrée initiale'),
        ('retour_produit', 'Retour produit en magasin'),
    ]
    article = forms.ModelChoiceField(queryset=Article.objects.filter(archive=False), label='Article')
    magasin = forms.ModelChoiceField(queryset=Magasin.objects.filter(actif=True), label='Magasin')
    emplacement = forms.ModelChoiceField(queryset=Emplacement.objects.filter(actif=True), required=False, label='Emplacement')
    quantite = forms.DecimalField(min_value=0, label='Quantité à entrer')
    type_entree = forms.ChoiceField(choices=TYPE_CHOICES, label='Type d’entrée')
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, allowed_magasins=None, initial_article=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_magasins is not None:
            self.fields['magasin'].queryset = allowed_magasins
            self.fields['emplacement'].queryset = Emplacement.objects.filter(magasin__in=allowed_magasins, actif=True)
        if initial_article:
            self.initial['article'] = initial_article

class InventoryAdjustmentForm''', forms, flags=re.S)
    forms = re.sub(r'class InventoryAdjustmentForm\(forms\.Form\):.*?\n\nclass UserVisibilityForm', r'''class InventoryAdjustmentForm(forms.Form):
    """Mise à niveau ponctuelle du stock réel après inventaire physique."""
    TYPE_CHOICES = [('inventaire', 'Inventaire / comptage physique'), ('reassort', 'Réassort / entrée magasin')]
    operation_type = forms.ChoiceField(choices=TYPE_CHOICES, label='Type d’opération')
    ean = forms.CharField(required=False, label='EAN / code-barres tablette')
    article = forms.ModelChoiceField(queryset=Article.objects.filter(archive=False), label='Article')
    magasin = forms.ModelChoiceField(queryset=Magasin.objects.filter(actif=True), label='Magasin')
    emplacement = forms.ModelChoiceField(queryset=Emplacement.objects.filter(actif=True), required=False, label='Emplacement constaté')
    stock_reel_compte = forms.DecimalField(min_value=0, label='Stock réel compté ou quantité à entrer')
    qte_ok = forms.DecimalField(min_value=0, required=False, label='Quantité disponible / OK')
    qte_use = forms.DecimalField(min_value=0, required=False, label='Quantité usée')
    stock_hs = forms.DecimalField(min_value=0, required=False, label='Quantité HS')
    stock_perdu = forms.DecimalField(min_value=0, required=False, label='Quantité perdue')
    stock_mini = forms.DecimalField(min_value=0, required=False, label='Stock mini corrigé')
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label='Commentaire inventaire')

    def __init__(self, *args, allowed_magasins=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_magasins is not None:
            self.fields['magasin'].queryset = allowed_magasins
            self.fields['emplacement'].queryset = Emplacement.objects.filter(magasin__in=allowed_magasins, actif=True)

class UserVisibilityForm''', forms, flags=re.S)
    forms_path.write_text(forms, encoding='utf-8')

# ---------------------------------------------------------------------------
# PedaShop : service import avancé
# ---------------------------------------------------------------------------
services_path = p('pedashop-app/pedashop/services.py')
if services_path.exists():
    services = services_path.read_text(encoding='utf-8')
    if 'def commit_import_advanced' not in services:
        services += r'''


@transaction.atomic
def commit_import_advanced(rows: List[dict], magasin, actor=None, check_stock_consistency: bool = False,
                           mode: str = 'append_only', key_field: str = 'reference_interne',
                           ignore_blank: bool = True) -> dict:
    """Import PedaShop multi-mode.

    Modes :
    - append_only : ajoute uniquement les absents, ne modifie pas l'existant.
    - upsert : met à jour selon une clé et ajoute les absents.
    - replace_all : remplace la base articles/stocks PedaShop, à utiliser avec confirmation côté vue.
    - simulation : calcule le rapport sans écrire.
    """
    from .models import Article, Emplacement, StockArticleMagasin, MouvementStock
    allowed_keys = {'reference_interne', 'reference_fabricant', 'code_ean', 'designation'}
    if key_field not in allowed_keys:
        key_field = 'reference_interne'
    dry_run = mode == 'simulation'
    report = {
        'mode': mode,
        'key_field': key_field,
        'created_articles': 0,
        'updated_articles': 0,
        'skipped_articles': 0,
        'created_stocks': 0,
        'updated_stocks': 0,
        'deleted_articles': 0,
        'errors': [],
        'warnings': [],
    }
    if mode == 'replace_all' and not dry_run:
        report['deleted_articles'] = Article.objects.count()
        StockArticleMagasin.objects.all().delete()
        Article.objects.all().delete()

    article_fields = [
        'reference_fabricant', 'fabricant', 'designation', 'description', 'code_ean', 'unite',
        'categorie', 'sous_categorie', 'prix_coutant', 'prix_vente', 'tva', 'substituable',
        'fournisseur', 'marche', 'archive'
    ]
    for row in rows:
        ref = row.get('reference_interne')
        if not ref:
            report['errors'].append(f"Ligne {row.get('line')}: code produit manquant")
            continue
        key_value = row.get(key_field) or ref
        qs = Article.objects.filter(**{key_field: key_value})
        if qs.count() > 1:
            report['warnings'].append(f"Ligne {row.get('line')}: clé {key_field}={key_value} non unique ; premier article utilisé.")
        article = qs.first()
        exists = article is not None

        if exists and mode == 'append_only':
            report['skipped_articles'] += 1
            continue

        if check_stock_consistency:
            detail = row.get('qte_ok', 0) + row.get('qte_use', 0) + row.get('stock_hs', 0)
            if detail and detail != row.get('stock_reel'):
                report['warnings'].append(f"Ligne {row.get('line')}: incohérence stock. Stock={row.get('stock_reel')} ; OK+Usé+HS={detail}.")

        if not exists:
            if dry_run:
                report['created_articles'] += 1
                continue
            article = Article(reference_interne=ref)
            for f in article_fields:
                setattr(article, f, row.get(f, getattr(article, f, '')))
            article.designation = article.designation or ref
            article.save()
            report['created_articles'] += 1
        else:
            if dry_run:
                report['updated_articles'] += 1
            else:
                changed = []
                for f in article_fields:
                    value = row.get(f)
                    if ignore_blank and value in ['', None]:
                        continue
                    if value is not None and getattr(article, f) != value:
                        setattr(article, f, value)
                        changed.append(f)
                if changed:
                    article.save()
                report['updated_articles'] += 1

        if dry_run:
            continue
        location_code = row.get('emplacement') or 'A_DEFINIR'
        emplacement, _ = Emplacement.objects.get_or_create(
            magasin=magasin,
            code=location_code,
            defaults={'nom': location_code, 'description': 'Créé automatiquement lors de l’import Excel.'}
        )
        stock, created_stock = StockArticleMagasin.objects.get_or_create(article=article, magasin=magasin)
        before = stock.stock_reel
        stock.emplacement = emplacement
        stock.stock_reel = row.get('stock_reel') or 0
        stock.stock_minimum = row.get('stock_minimum') or 0
        stock.stock_reserve_demande = row.get('stock_reserve_demande') or 0
        stock.stock_temporairement_sorti = row.get('stock_temporairement_sorti') or 0
        stock.qte_ok = row.get('qte_ok') or 0
        stock.qte_use = row.get('qte_use') or 0
        stock.stock_hs = row.get('stock_hs') or 0
        stock.save()
        report['created_stocks' if created_stock else 'updated_stocks'] += 1
        if before != stock.stock_reel:
            MouvementStock.objects.create(
                article=article,
                magasin_destination=magasin,
                emplacement_destination=emplacement,
                type_mouvement='import_excel',
                quantite=stock.stock_reel - before,
                stock_avant=before,
                stock_apres=stock.stock_reel,
                utilisateur=actor,
                commentaire=f'Import Excel mode={mode} clé={key_field}',
            )
    return report
'''
    services_path.write_text(services, encoding='utf-8')

# ---------------------------------------------------------------------------
# PedaShop : vues imports/filtres/API/stock
# ---------------------------------------------------------------------------
views_path = p('pedashop-app/pedashop/views.py')
if views_path.exists():
    views = views_path.read_text(encoding='utf-8')
    views = views.replace('from .services import affect_line_to_projection, commit_import, load_import_rows, recalculate_stock_alerts',
                          'from .services import affect_line_to_projection, commit_import, commit_import_advanced, load_import_rows, recalculate_stock_alerts')
    # article detail: pas besoin de changer la vue, template envoie GET article
    # stock_entry avec préremplissage article
    views = re.sub(r'@require_http_methods\(\[\'GET\', \'POST\'\]\)\n@transaction\.atomic\ndef stock_entry\(request\):.*?\n\s*return render\(request, \'pedashop/form\.html\', \{\'form\': form, \'title\': \'Entrée en magasin / réassort\'\}\)', r'''@require_http_methods(['GET', 'POST'])
@transaction.atomic
def stock_entry(request):
    """Entrée en magasin : réassort acheté, retour produit ou stock initial."""
    user = require_storekeeper(request)
    if not user or not _can_act_as_storekeeper(request, user):
        return redirect('pedashop_login')
    initial_article = request.GET.get('article')
    form = StockEntryForm(request.POST or None, allowed_magasins=_visible_magasins(user), initial_article=initial_article)
    if request.method == 'POST' and form.is_valid():
        article = form.cleaned_data['article']; magasin = form.cleaned_data['magasin']; q = form.cleaned_data['quantite']
        stock, _ = StockArticleMagasin.objects.get_or_create(article=article, magasin=magasin)
        before = stock.stock_reel
        stock.stock_reel += q
        if form.cleaned_data.get('emplacement'):
            stock.emplacement = form.cleaned_data['emplacement']
        stock.save()
        type_mv = form.cleaned_data['type_entree'] if form.cleaned_data['type_entree'] in dict(MouvementStock.TYPE_CHOICES) else 'reception_fournisseur'
        MouvementStock.objects.create(article=article, magasin_destination=magasin, emplacement_destination=stock.emplacement, type_mouvement=type_mv, quantite=q, stock_avant=before, stock_apres=stock.stock_reel, utilisateur=user, commentaire=form.cleaned_data.get('commentaire', ''))
        recalculate_stock_alerts(); messages.success(request, 'Entrée stock enregistrée.')
        return redirect('pedashop_stock_list')
    return render(request, 'pedashop/stock_entry.html', {'form': form, 'title': 'Entrée en magasin / réassort'})''', views, flags=re.S)
    views = re.sub(r'@require_http_methods\(\[\'GET\', \'POST\'\]\)\n@transaction\.atomic\ndef inventory_adjustment\(request\):.*?\n\s*return render\(request, \'pedashop/inventory_adjustment\.html\', \{\'form\': form, \'recent\': recent\}\)', r'''@require_http_methods(['GET', 'POST'])
@transaction.atomic
def inventory_adjustment(request):
    """Inventaire ou réassort depuis une page unique."""
    user = require_storekeeper(request)
    if not user or not _can_act_as_storekeeper(request, user):
        return redirect('pedashop_login')
    form = InventoryAdjustmentForm(request.POST or None, allowed_magasins=_visible_magasins(user))
    recent = MouvementStock.objects.filter(type_mouvement__in=['correction_inventaire', 'reception_fournisseur']).select_related('article', 'magasin_destination', 'utilisateur')[:25]
    if request.method == 'POST' and form.is_valid():
        article = form.cleaned_data['article']
        ean = form.cleaned_data.get('ean')
        if ean:
            article = Article.objects.filter(Q(code_ean=ean) | Q(reference_interne=ean) | Q(code_barres_interne=ean)).first() or article
        magasin = form.cleaned_data['magasin']
        stock, _ = StockArticleMagasin.objects.get_or_create(article=article, magasin=magasin)
        before = stock.stock_reel
        qty = form.cleaned_data['stock_reel_compte']
        if form.cleaned_data['operation_type'] == 'reassort':
            stock.stock_reel += qty
            mv_type = 'reception_fournisseur'
            mv_qty = qty
        else:
            stock.stock_reel = qty
            mv_type = 'correction_inventaire'
            mv_qty = qty - before
        if form.cleaned_data.get('qte_ok') is not None:
            stock.qte_ok = form.cleaned_data['qte_ok']
        if form.cleaned_data.get('qte_use') is not None:
            stock.qte_use = form.cleaned_data['qte_use']
        if form.cleaned_data.get('stock_hs') is not None:
            stock.stock_hs = form.cleaned_data['stock_hs']
        if form.cleaned_data.get('stock_perdu') is not None:
            stock.stock_perdu = form.cleaned_data['stock_perdu']
        if form.cleaned_data.get('stock_mini') is not None:
            stock.stock_minimum = form.cleaned_data['stock_mini']
        if form.cleaned_data.get('emplacement'):
            stock.emplacement = form.cleaned_data['emplacement']
        stock.save()
        MouvementStock.objects.create(article=article, magasin_destination=magasin, type_mouvement=mv_type, quantite=mv_qty, stock_avant=before, stock_apres=stock.stock_reel, utilisateur=user, commentaire=form.cleaned_data.get('commentaire', ''))
        recalculate_stock_alerts(); messages.success(request, 'Opération stock enregistrée.')
        return redirect('pedashop_inventory_adjustment')
    return render(request, 'pedashop/inventory_adjustment.html', {'form': form, 'recent': recent})''', views, flags=re.S)
    # import_excel avancé
    views = re.sub(r'@require_http_methods\(\[\'GET\', \'POST\'\]\)\ndef import_excel\(request\):.*?\n\s*return render\(request, \'pedashop/import_excel\.html\', \{\'form\': locals\(\)\.get\(\'form\', ExcelImportForm\(allowed_magasins=_visible_magasins\(user\)\)\), \'preview\': preview, \'report\': report\}\)', r'''@require_http_methods(['GET', 'POST'])
def import_excel(request):
    user = require_login(request)
    if not user or not (user.is_admin_like or user.is_teacher_like):
        messages.error(request, 'Import articles réservé aux professeurs ou administrateurs PedaShop.')
        return redirect('pedashop_login' if not user else 'pedashop_dashboard')
    preview = None
    report = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'commit':
            staged = request.session.get('pedashop_import_file')
            magasin_id = request.session.get('pedashop_import_magasin')
            sheet = request.session.get('pedashop_import_sheet')
            check = request.session.get('pedashop_import_check_stock', False)
            mode = request.session.get('pedashop_import_mode', 'append_only')
            key = request.session.get('pedashop_import_key', 'reference_interne')
            ignore_blank = request.session.get('pedashop_import_ignore_blank', True)
            if staged and magasin_id:
                rows, info = load_import_rows(staged, sheet)
                report = commit_import_advanced(rows, get_object_or_404(Magasin, pk=magasin_id), actor=user, check_stock_consistency=check, mode=mode, key_field=key, ignore_blank=ignore_blank)
                messages.success(request, f"Import traité : {report['created_articles']} créés, {report['updated_articles']} modifiés, {report['skipped_articles']} ignorés, {len(report['errors'])} erreurs.")
            else:
                messages.error(request, 'Aucun aperçu d’import à valider.')
        else:
            form = ExcelImportForm(request.POST, request.FILES, allowed_magasins=_visible_magasins(user))
            if form.is_valid():
                if form.cleaned_data['mode_import'] == 'replace_all' and form.cleaned_data.get('confirmation_remplacement') != 'REMPLACER':
                    messages.error(request, 'Pour un remplacement total, saisir exactement REMPLACER dans le champ de confirmation.')
                else:
                    upload = form.cleaned_data['fichier']
                    suffix = Path(upload.name).suffix or '.xlsx'
                    target_dir = Path(settings.MEDIA_ROOT) / 'pedashop_imports'
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target = target_dir / f'import_{timezone.now():%Y%m%d_%H%M%S}{suffix}'
                    with target.open('wb') as f:
                        for chunk in upload.chunks():
                            f.write(chunk)
                    rows, info = load_import_rows(str(target), form.cleaned_data.get('feuille'))
                    preview = {'rows': rows[:20], 'info': info, 'count': len(rows), 'mode': form.cleaned_data['mode_import'], 'key': form.cleaned_data['cle_import']}
                    request.session['pedashop_import_file'] = str(target)
                    request.session['pedashop_import_magasin'] = form.cleaned_data['magasin'].id
                    request.session['pedashop_import_sheet'] = form.cleaned_data.get('feuille') or ''
                    request.session['pedashop_import_check_stock'] = bool(form.cleaned_data.get('verifier_coherence_stock'))
                    request.session['pedashop_import_mode'] = form.cleaned_data['mode_import']
                    request.session['pedashop_import_key'] = form.cleaned_data['cle_import']
                    request.session['pedashop_import_ignore_blank'] = bool(form.cleaned_data.get('ignorer_cellules_vides'))
            else:
                messages.error(request, 'Formulaire import invalide.')
    else:
        form = ExcelImportForm(allowed_magasins=_visible_magasins(user))
    return render(request, 'pedashop/import_excel.html', {'form': locals().get('form', ExcelImportForm(allowed_magasins=_visible_magasins(user))), 'preview': preview, 'report': report})''', views, flags=re.S)
    if 'def api_article_search' not in views:
        api = r'''


def api_article_search(request):
    user = current_user(request)
    q = (request.GET.get('q') or '').strip()
    qs = Article.objects.filter(archive=False)
    if q:
        qs = qs.filter(Q(reference_interne__icontains=q) | Q(reference_fabricant__icontains=q) | Q(designation__icontains=q) | Q(code_ean__icontains=q) | Q(code_barres_interne__icontains=q))
    rows = []
    for a in qs.order_by('reference_interne')[:20]:
        rows.append({'id': a.id, 'reference_interne': a.reference_interne, 'reference_fabricant': a.reference_fabricant, 'designation': a.designation, 'code_ean': a.code_ean, 'label': f'{a.reference_interne} — {a.designation}'})
    return JsonResponse({'results': rows})


def api_magasin_search(request):
    user = current_user(request)
    q = (request.GET.get('q') or '').strip()
    qs = _visible_magasins(user)
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(nom__icontains=q))
    return JsonResponse({'results': [{'id': m.id, 'code': m.code, 'nom': m.nom, 'label': f'{m.code} — {m.nom}'} for m in qs[:20]]})


def api_emplacement_search(request):
    user = current_user(request)
    q = (request.GET.get('q') or '').strip()
    magasin_id = request.GET.get('magasin_id')
    qs = Emplacement.objects.filter(actif=True)
    if magasin_id:
        qs = qs.filter(magasin_id=magasin_id)
    else:
        qs = qs.filter(magasin__in=_visible_magasins(user))
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(nom__icontains=q) | Q(magasin__code__icontains=q))
    return JsonResponse({'results': [{'id': e.id, 'code': e.code, 'nom': e.nom, 'magasin_id': e.magasin_id, 'label': f'{e.magasin.code}/{e.code} — {e.nom}'} for e in qs.select_related('magasin')[:20]]})
'''
        views = views.replace('\ndef user_list(request):', api + '\n\ndef user_list(request):')
    views_path.write_text(views, encoding='utf-8')

# ---------------------------------------------------------------------------
# PedaShop URLs : API dynamiques et suppression ancien admin SQL
# ---------------------------------------------------------------------------
urls_path = p('pedashop-app/pedashop/urls.py')
if urls_path.exists():
    urls = urls_path.read_text(encoding='utf-8')
    urls = re.sub(r"\n\s*path\('admin-sql/.*?\),", '', urls)
    if "api/articles/search" not in urls:
        urls = urls.replace("path('api/internal/sync-lp-core/', views.internal_sync_lp_core, name='pedashop_internal_sync_lp_core'),",
            "path('api/internal/sync-lp-core/', views.internal_sync_lp_core, name='pedashop_internal_sync_lp_core'),\n    path('api/articles/search/', views.api_article_search, name='pedashop_api_article_search'),\n    path('api/magasins/search/', views.api_magasin_search, name='pedashop_api_magasin_search'),\n    path('api/emplacements/search/', views.api_emplacement_search, name='pedashop_api_emplacement_search'),")
    urls_path.write_text(urls, encoding='utf-8')

# ---------------------------------------------------------------------------
# PedaShop templates
# ---------------------------------------------------------------------------
write('pedashop-app/pedashop/templates/pedashop/base.html', r'''
{% load static %}
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
    {% if pedashop_current_user %}<span class="role-pill">{{ request.session.pedashop_active_role|default:'utilisateur' }}</span>{% endif %}
  </div>
  <nav>
    <a href="{% url 'pedashop_dashboard' %}">Tableau de bord</a>
    <a href="{% url 'pedashop_stock_list' %}">Stock</a>
    {% if pedashop_current_user %}
      <a href="{% url 'pedashop_article_list' %}">Articles</a>
      <a href="{% url 'pedashop_bon_list' %}">Bons</a>
      <details class="admin-dropdown"><summary>Actions magasinier</summary><div class="admin-dropdown-menu">
        <a class="admin-menu-item" href="{% url 'pedashop_inventory_adjustment' %}">Inventaire</a>
        <a class="admin-menu-item" href="{% url 'pedashop_stock_entry' %}">Entrée / réassort</a>
        <a class="admin-menu-item" href="{% url 'pedashop_movement_list' %}">Mouvements</a>
        <a class="admin-menu-item" href="{% url 'pedashop_alert_list' %}">Alertes</a>
        <a class="admin-menu-item" href="{% url 'pedashop_reclamation_list' %}">Réclamations</a>
        <a class="admin-menu-item" href="{% url 'pedashop_affichage' %}">Affichage dynamique</a>
      </div></details>
      {% if pedashop_current_user.is_teacher_like or pedashop_current_user.is_admin_like %}
      <details class="admin-dropdown"><summary>Administration</summary><div class="admin-dropdown-menu">
        <a class="admin-menu-item" href="{% url 'pedashop_import_excel' %}">Import articles</a>
        <a class="admin-menu-item" href="{% url 'pedashop_articles_template_xlsx' %}">Modèle import articles</a>
        <a class="admin-menu-item" href="{% url 'pedashop_articles_export_xlsx' %}">Export articles</a>
        <a class="admin-menu-item" href="{% url 'pedashop_magasin_list' %}">Magasins</a>
        <a class="admin-menu-item" href="{% url 'pedashop_emplacement_list' %}">Emplacements</a>
        <a class="admin-menu-item" href="{% url 'pedashop_user_list' %}">Utilisateurs</a>
        <a class="admin-menu-item" href="{% url 'pedashop_projection_list' %}">Pré-réservations TP</a>
        <a class="admin-menu-item" href="{% url 'pedashop_consultation_list' %}">Consultations</a>
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
    {% endif %}
    {% if pedashop_current_user %}<a href="{% url 'pedashop_logout' %}">Déconnexion {{ pedashop_current_user.username }}</a>{% else %}<a href="{% url 'pedashop_login' %}">Connexion</a>{% endif %}
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
''')

write('pedashop-app/pedashop/templates/pedashop/article_detail.html', r'''
{% extends 'pedashop/base.html' %}
{% block content %}<h1>{{ article.reference_interne }} — {{ article.designation }}</h1><div class="grid-2"><div class="card"><h2>Fiche article</h2>{% if article.photo %}<img src="{{ article.photo.url }}" style="max-width:220px">{% endif %}<p><b>EAN / code tablette :</b> {{ article.code_ean }}</p><p><b>Fabricant :</b> {{ article.fabricant }}</p><p><b>Réf. constructeur :</b> {{ article.reference_fabricant }}</p><p><b>Catégorie :</b> {{ article.categorie }}</p><p><b>Sous-catégorie :</b> {{ article.sous_categorie }}</p><p><b>Marché :</b> {{ article.marche }}</p><p><b>Substituable :</b> {{ article.substituable|yesno:'Oui,Non' }}</p>{% if can_edit_articles %}<a class="btn" href="{% url 'pedashop_article_edit' article.pk %}">Modifier</a>{% endif %} <a class="btn primary" href="{% url 'pedashop_stock_entry' %}?article={{ article.pk }}">Entrée / réassort</a></div><div class="card"><h2>Stocks par magasin</h2><table><thead><tr><th>Magasin</th><th>Empl.</th><th>En stock</th><th>Réservé</th><th>Prépa</th><th>Extérieur</th><th>Dispo</th><th>Usé</th><th>HS</th><th>Perdu</th></tr></thead><tbody>{% for s in stocks %}<tr><td>{{ s.magasin.code }}</td><td>{{ s.emplacement }}</td><td>{{ s.stock_reel }}</td><td>{{ s.reserve_total }}</td><td>{{ s.stock_en_preparation }}</td><td>{{ s.stock_temporairement_sorti }}</td><td>{{ s.stock_disponible }}</td><td>{{ s.qte_use }}</td><td>{{ s.stock_hs }}</td><td>{{ s.stock_perdu }}</td></tr>{% endfor %}</tbody></table></div></div><section class="card"><h2>Retours prévus</h2><table><thead><tr><th>Bon</th><th>Quantité</th><th>Retour prévu</th><th>Statut</th></tr></thead><tbody>{% for r in retours %}<tr><td>{{ r.ligne_bon.bon.code }}</td><td>{{ r.quantite_attendue }}</td><td>{{ r.date_retour_prevue }}</td><td>{{ r.get_statut_display }}</td></tr>{% empty %}<tr><td colspan="4">Aucun retour attendu.</td></tr>{% endfor %}</tbody></table></section>{% endblock %}
''')

filter_js = r'''
<script>
async function lpSearch(url, q){
  const r = await fetch(url + '?q=' + encodeURIComponent(q));
  if(!r.ok) return [];
  const data = await r.json();
  return data.results || [];
}
function selectOptionByValue(selectName, value){
  const select = document.querySelector('[name="'+selectName+'"]');
  if(!select) return;
  select.value = String(value);
  select.dispatchEvent(new Event('change', {bubbles:true}));
}
function setupSuggest(inputId, boxId, url, targetName, renderExtra){
  const input=document.getElementById(inputId), box=document.getElementById(boxId);
  if(!input || !box) return;
  input.addEventListener('input', async ()=>{
    const q=input.value.trim();
    box.innerHTML='';
    if(q.length < 1) return;
    const rows=await lpSearch(url, q);
    rows.forEach(row=>{
      const btn=document.createElement('button'); btn.type='button'; btn.className='suggestion-row';
      btn.textContent=row.label;
      btn.addEventListener('click', ()=>{ selectOptionByValue(targetName, row.id); input.value=row.label; box.innerHTML=''; if(renderExtra) renderExtra(row); });
      box.appendChild(btn);
    });
  });
}
setupSuggest('article-search','article-suggestions','{% url "pedashop_api_article_search" %}','article', row=>{
  const info=document.getElementById('article-info'); if(info) info.textContent='Code : '+row.reference_interne+' | Réf. : '+(row.reference_fabricant||'')+' | EAN : '+(row.code_ean||'');
});
setupSuggest('magasin-search','magasin-suggestions','{% url "pedashop_api_magasin_search" %}','magasin');
setupSuggest('emplacement-search','emplacement-suggestions','{% url "pedashop_api_emplacement_search" %}','emplacement');
const ean=document.querySelector('[name="ean"]'); if(ean){ ean.focus(); }
</script>
'''

write('pedashop-app/pedashop/templates/pedashop/stock_entry.html', r'''
{% extends 'pedashop/base.html' %}
{% block content %}
<h1>Entrée en magasin / réassort</h1>
<div class="card">
<p class="muted">Recherche dynamique : code produit, référence fabricant, désignation ou code-barres. Le scan d’une scannette USB fonctionne comme une saisie clavier dans le champ de recherche.</p>
<form method="post">{% csrf_token %}
  <label>Recherche article / code-barres<input id="article-search" autocomplete="off" placeholder="Scanner ou saisir code, référence, désignation"></label><div id="article-suggestions" class="suggestion-box"></div><p id="article-info" class="muted"></p>
  <label>Recherche magasin<input id="magasin-search" autocomplete="off" placeholder="Code ou nom du magasin"></label><div id="magasin-suggestions" class="suggestion-box"></div>
  <label>Recherche emplacement<input id="emplacement-search" autocomplete="off" placeholder="Code ou nom de l’emplacement"></label><div id="emplacement-suggestions" class="suggestion-box"></div>
  {{ form.as_p }}
  <button class="btn primary" type="submit">Enregistrer</button> <a class="btn" href="javascript:history.back()">Retour</a>
</form>
</div>
'''+filter_js+r'''
{% endblock %}
''')

write('pedashop-app/pedashop/templates/pedashop/inventory_adjustment.html', r'''
{% extends 'pedashop/base.html' %}
{% block content %}
<h1>Inventaire / réassort</h1><div class="alert">Inventaire : remplace uniquement le stock physiquement en magasin. Les réservations, préparations et sorties temporaires avec retour prévu ne sont pas modifiées. Le matériel dehors doit revenir via un bon de retour.</div>
<div class="grid-2"><section class="card"><h2>Nouvelle opération</h2><p class="muted">Recherche dynamique par code, référence, désignation, EAN ou scannette code-barres.</p><form method="post">{% csrf_token %}
  <label>Recherche article / code-barres<input id="article-search" autocomplete="off" placeholder="Scanner ou saisir code, référence, désignation"></label><div id="article-suggestions" class="suggestion-box"></div><p id="article-info" class="muted"></p>
  <label>Recherche magasin<input id="magasin-search" autocomplete="off" placeholder="Code ou nom du magasin"></label><div id="magasin-suggestions" class="suggestion-box"></div>
  <label>Recherche emplacement<input id="emplacement-search" autocomplete="off" placeholder="Code ou nom de l’emplacement"></label><div id="emplacement-suggestions" class="suggestion-box"></div>
  {{ form.as_p }}
  <button class="btn primary">Enregistrer</button></form></section><section class="card"><h2>Dernières opérations</h2><table><thead><tr><th>Date</th><th>Article</th><th>Écart / Qté</th><th>Utilisateur</th></tr></thead><tbody>{% for m in recent %}<tr><td>{{ m.date }}</td><td>{{ m.article.reference_interne }}</td><td>{{ m.quantite }}</td><td>{{ m.utilisateur }}</td></tr>{% empty %}<tr><td colspan="4">Aucune opération.</td></tr>{% endfor %}</tbody></table></section></div>
'''+filter_js+r'''
{% endblock %}
''')

write('pedashop-app/pedashop/templates/pedashop/import_excel.html', r'''
{% extends 'pedashop/base.html' %}
{% block content %}
<h1>Import Excel PedaShop</h1>
<div class="card"><h2>Modes d’import</h2><ul><li><strong>Remplacement total</strong> : remplace la base articles PedaShop après confirmation <code>REMPLACER</code>.</li><li><strong>Mise à jour par clé</strong> : compare selon code, référence, EAN ou désignation ; modifie si existant, ajoute sinon.</li><li><strong>Ajout uniquement</strong> : ajoute les articles absents et ne modifie pas les existants.</li><li><strong>Simulation</strong> : calcule le rapport sans écrire.</li></ul><p><a class="btn" href="{% url 'pedashop_articles_template_xlsx' %}">Télécharger le modèle import articles</a></p></div>
<div class="card"><form method="post" enctype="multipart/form-data">{% csrf_token %}{{ form.as_p }}<button class="btn primary" type="submit">Prévisualiser</button></form></div>
{% if preview %}<div class="card"><h2>Aperçu — {{ preview.count }} lignes</h2><p class="muted">Feuille : {{ preview.info.sheet }} | Mode : {{ preview.mode }} | Clé : {{ preview.key }}</p><table><thead><tr><th>Code</th><th>Désignation</th><th>Fabricant</th><th>Stock</th><th>Mini</th></tr></thead><tbody>{% for r in preview.rows %}<tr><td>{{ r.reference_interne }}</td><td>{{ r.designation }}</td><td>{{ r.fabricant }}</td><td>{{ r.stock_reel }}</td><td>{{ r.stock_minimum }}</td></tr>{% endfor %}</tbody></table><form method="post">{% csrf_token %}<input type="hidden" name="action" value="commit"><button class="btn orange" type="submit">Valider l’import</button></form></div>{% endif %}
{% if report %}<div class="card"><h2>Rapport</h2><p>Mode : {{ report.mode }} — Clé : {{ report.key_field }}</p><p>Articles créés : {{ report.created_articles }}</p><p>Articles modifiés : {{ report.updated_articles }}</p><p>Articles ignorés : {{ report.skipped_articles }}</p><p>Stocks créés : {{ report.created_stocks }}</p><p>Stocks modifiés : {{ report.updated_stocks }}</p><p>Articles supprimés : {{ report.deleted_articles }}</p><p>Erreurs : {{ report.errors|length }}</p><ul>{% for e in report.errors %}<li>{{ e }}</li>{% endfor %}</ul><p>Avertissements : {{ report.warnings|length }}</p><ul>{% for w in report.warnings %}<li>{{ w }}</li>{% endfor %}</ul></div>{% endif %}
{% endblock %}
''')

# supprimer template admin SQL PedaShop non routé
sql_tpl = p('pedashop-app/pedashop/templates/pedashop/sql_database.html')
if sql_tpl.exists():
    sql_tpl.unlink()

# CSS commun suggestions / menus
css_path = p('pedashop-app/pedashop/static/pedashop/pedashop.css')
if css_path.exists():
    css = css_path.read_text(encoding='utf-8')
    if '.suggestion-box' not in css:
        css += r'''

.suggestion-box{display:flex;flex-direction:column;gap:.35rem;margin:.35rem 0 .75rem 0;max-height:220px;overflow:auto}
.suggestion-row{width:100%;text-align:left;background:#f8fbff;border:1px solid #cbd5e1;border-radius:6px;padding:.45rem .65rem;cursor:pointer;color:#0f172a}
.suggestion-row:hover{background:#e0f2fe;border-color:#38bdf8}
.admin-dropdown{position:relative;display:inline-block}
.admin-dropdown-menu{position:absolute;right:0;background:white;color:#0f172a;border:1px solid #cbd5e1;border-radius:8px;box-shadow:0 12px 30px rgba(15,23,42,.18);min-width:220px;z-index:50;padding:.35rem}
.admin-menu-item{display:block;padding:.45rem .7rem;color:#0f172a;text-decoration:none;border-radius:6px}
.admin-menu-item:hover{background:#e0f2fe}
'''
        css_path.write_text(css, encoding='utf-8')

core_css = p('lp-core-app/core/static/core/style.css')
if core_css.exists():
    css = core_css.read_text(encoding='utf-8')
    if '.lp-dyn-filter' not in css:
        css += r'''

.lp-dyn-filter,.choice-filter{width:100%;max-width:520px;margin:.5rem 0 1rem 0;padding:.55rem .7rem;border:1px solid #cbd5e1;border-radius:6px}
'''
        core_css.write_text(css, encoding='utf-8')

# ---------------------------------------------------------------------------
# Correction robuste chemins .env update/migration si scripts présents
# ---------------------------------------------------------------------------
for sh in ['scripts/migrate_all.sh', 'update.sh']:
    path = p(sh)
    if path.exists():
        txt = path.read_text(encoding='utf-8')
        if '/home/user/docker/lp-gestion-atelier/.env' in txt or 'dirname "$0"' in txt:
            txt = txt.replace('/home/user/docker/lp-gestion-atelier/.env', '${ROOT_DIR}/.env')
        if 'ROOT_DIR=' not in txt.split('\n', 15)[0:15]:
            txt = txt.replace('set -euo pipefail', 'set -euo pipefail\nSCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\nROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"\n[[ -f "${ROOT_DIR}/docker-compose.yml" ]] || ROOT_DIR="${SCRIPT_DIR}"', 1)
        path.write_text(txt, encoding='utf-8')

PY

echo "[RC8] Nettoyage caches Python"
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

echo "[RC8] Vérification syntaxe Python minimale"
python3 -m py_compile pedashop-app/pedashop/forms.py pedashop-app/pedashop/services.py pedashop-app/pedashop/views.py lp-core-app/core/views.py

echo "[RC8] Vérification syntaxe shell"
bash -n update.sh 2>/dev/null || true
bash -n scripts/migrate_all.sh 2>/dev/null || true

echo "[RC8] Recalcul CHECKSUMS.sha256"
python3 <<'PY'
from pathlib import Path
import hashlib
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
files=sorted(files,key=lambda p: str(p).replace('\\','/'))
with open('CHECKSUMS.sha256','w',encoding='utf-8',newline='\n') as out:
    for path in files:
        h=hashlib.sha256()
        with open(path,'rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''):
                h.update(chunk)
        out.write(f"{h.hexdigest()}  ./{str(path).replace('\\','/')}\n")
PY
sha256sum -c CHECKSUMS.sha256 2>&1 | grep -E 'FAILED|WARNING|No such file|did NOT match' && exit 1 || echo "CHECKSUMS OK"

echo "[RC8] Patch appliqué. Commit conseillé :"
echo "git add -A && git commit -m 'RC8 PedaShop imports filtres et LP Core magasins modules'"
