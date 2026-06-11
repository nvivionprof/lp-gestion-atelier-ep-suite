#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
if [[ ! -f "docker-compose.yml" || ! -d "pfmp-app/pfmp_manager" ]]; then
  echo "Erreur : lance ce script depuis la racine du dépôt LP Gestion Atelier EP Suite."
  exit 1
fi

CURRENT_VERSION="$(cat VERSION 2>/dev/null || true)"
echo "Version détectée : ${CURRENT_VERSION:-inconnue}"
if [[ "$CURRENT_VERSION" != "V0.0.1-RC12" && "$CURRENT_VERSION" != "V0.0.1-RC13" ]]; then
  echo "Attention : ce patch RC13 a été préparé pour une base RC12. Application non bloquante, mais contrôle obligatoire après patch."
fi

python3 <<'PY'
from pathlib import Path
import json

ROOT = Path('.')
VERSION = 'V0.0.1-RC13'

for rel in ['VERSION', 'VERSION.txt', '.suite-target-version']:
    p = ROOT / rel
    if p.exists():
        p.write_text(VERSION + '\n', encoding='utf-8')

manifest = ROOT / 'manifest.json'
if manifest.exists():
    try:
        data = json.loads(manifest.read_text(encoding='utf-8'))
    except Exception:
        data = {}
    data['version'] = VERSION
    data['suite_version'] = VERSION
    data['release'] = 'RC13 PFMP Manager historique'
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# --- PFMP urls.py : ajout route historique ---
urls = ROOT / 'pfmp-app/pfmp_manager/urls.py'
text = urls.read_text(encoding='utf-8')
if "name='pfmp_history'" not in text:
    needle = " path('annonces/',views.announcement_list,name='pfmp_announcement_list'),"
    replacement = " path('historique/',views.history_view,name='pfmp_history'),\n" + needle
    if needle in text:
        text = text.replace(needle, replacement)
    else:
        text = text.replace("]", " path('historique/',views.history_view,name='pfmp_history'),\n]")
    urls.write_text(text, encoding='utf-8')

# --- PFMP base.html : ajout lien historique dans le menu principal ---
base = ROOT / 'pfmp-app/pfmp_manager/templates/pfmp_manager/base.html'
text = base.read_text(encoding='utf-8')
if "pfmp_history" not in text:
    needle = "<a href=\"{% url 'pfmp_assignment_list' %}\">Suivi élèves</a>"
    replacement = needle + "<a href=\"{% url 'pfmp_history' %}\">Historique</a>"
    text = text.replace(needle, replacement)
    base.write_text(text, encoding='utf-8')

# --- PFMP views.py : ajout history_view ---
views = ROOT / 'pfmp-app/pfmp_manager/views.py'
text = views.read_text(encoding='utf-8')
if 'def history_view(request):' not in text:
    marker = "def announcement_list(request):"
    history_code = r'''

def history_view(request):
    """Historique PFMP : affectations, démarches et annonces.

    Accès : prof/admin = historique complet ; élève = uniquement ses affectations et démarches.
    Les filtres utilisent le principe retenu dans la suite : champ libre + suggestions.
    """
    user = current_pfmp_user(request)
    if not user:
        return redirect('pfmp_login')

    q = (request.GET.get('q') or '').strip()
    student_q = (request.GET.get('student') or '').strip()
    company_q = (request.GET.get('company') or '').strip()
    period_q = (request.GET.get('period') or '').strip()
    formation_q = (request.GET.get('formation') or '').strip()
    status = (request.GET.get('status') or '').strip()
    event_type = (request.GET.get('event_type') or 'all').strip()

    assignments = StudentAssignment.objects.select_related('student', 'period', 'company', 'teacher').order_by('-updated_at')
    steps = StudentStep.objects.select_related('assignment', 'assignment__student', 'assignment__period', 'assignment__company', 'created_by').order_by('-date')
    announcements = CompanyAnnouncement.objects.select_related('company').prefetch_related('formations').order_by('-created_at')

    if not user.is_prof_like:
        assignments = assignments.filter(student=user)
        steps = steps.filter(assignment__student=user)
        announcements = announcements.filter(status='published')
        if user.formation_code:
            announcements = announcements.filter(Q(formations__isnull=True) | Q(formations__code=user.formation_code)).distinct()

    if q:
        assignments = assignments.filter(
            Q(student__first_name__icontains=q) | Q(student__last_name__icontains=q) | Q(student__code__icontains=q) |
            Q(period__title__icontains=q) | Q(company__name__icontains=q) | Q(student_comment__icontains=q) | Q(teacher_comment__icontains=q)
        )
        steps = steps.filter(
            Q(title__icontains=q) | Q(comment__icontains=q) | Q(assignment__student__first_name__icontains=q) |
            Q(assignment__student__last_name__icontains=q) | Q(assignment__company__name__icontains=q) | Q(assignment__period__title__icontains=q)
        )
        announcements = announcements.filter(Q(title__icontains=q) | Q(company__name__icontains=q) | Q(missions__icontains=q) | Q(expected_profile__icontains=q))

    if student_q:
        student_filter = Q(student__code__icontains=student_q) | Q(student__username__icontains=student_q) | Q(student__first_name__icontains=student_q) | Q(student__last_name__icontains=student_q)
        assignments = assignments.filter(student_filter)
        steps = steps.filter(Q(assignment__student__code__icontains=student_q) | Q(assignment__student__username__icontains=student_q) | Q(assignment__student__first_name__icontains=student_q) | Q(assignment__student__last_name__icontains=student_q))

    if company_q:
        assignments = assignments.filter(Q(company__name__icontains=company_q) | Q(company__city__icontains=company_q))
        steps = steps.filter(Q(assignment__company__name__icontains=company_q) | Q(assignment__company__city__icontains=company_q))
        announcements = announcements.filter(Q(company__name__icontains=company_q) | Q(company__city__icontains=company_q))

    if period_q:
        assignments = assignments.filter(period__title__icontains=period_q)
        steps = steps.filter(assignment__period__title__icontains=period_q)
        announcements = announcements.filter(period_text__icontains=period_q)

    if formation_q:
        assignments = assignments.filter(Q(student__formation_code__icontains=formation_q) | Q(period__formations__code__icontains=formation_q)).distinct()
        steps = steps.filter(Q(assignment__student__formation_code__icontains=formation_q) | Q(assignment__period__formations__code__icontains=formation_q)).distinct()
        announcements = announcements.filter(formations__code__icontains=formation_q).distinct()

    if status:
        assignments = assignments.filter(status=status)
        announcements = announcements.filter(status=status)

    events = []
    if event_type in {'all', 'assignment'}:
        for a in assignments[:300]:
            events.append({
                'type': 'Affectation',
                'date': a.updated_at,
                'sort': a.updated_at.isoformat() if a.updated_at else '',
                'title': f"{a.student.full_name} — {a.period.title}",
                'subtitle': a.company.name if a.company else 'Entreprise non renseignée',
                'status': a.get_status_display(),
                'detail': a.teacher_comment or a.student_comment or '',
            })
    if event_type in {'all', 'step'}:
        for s in steps[:300]:
            events.append({
                'type': 'Démarche',
                'date': s.date,
                'sort': s.date.isoformat() if s.date else '',
                'title': s.title,
                'subtitle': f"{s.assignment.student.full_name} — {s.assignment.period.title}",
                'status': s.get_step_type_display(),
                'detail': s.comment or '',
            })
    if event_type in {'all', 'announcement'}:
        for a in announcements[:200]:
            events.append({
                'type': 'Annonce',
                'date': a.created_at,
                'sort': a.created_at.isoformat() if a.created_at else '',
                'title': a.title,
                'subtitle': a.company.name,
                'status': a.get_status_display(),
                'detail': a.missions or a.expected_profile or '',
            })

    events.sort(key=lambda item: item.get('sort') or '', reverse=True)

    if request.GET.get('export') == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="pfmp_historique.csv"'
        response.write('\ufeff')
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['date', 'type', 'titre', 'contexte', 'statut', 'detail'])
        for event in events:
            writer.writerow([event['date'], event['type'], event['title'], event['subtitle'], event['status'], event['detail']])
        return response

    context = {
        'events': events[:500],
        'q': q,
        'student_q': student_q,
        'company_q': company_q,
        'period_q': period_q,
        'formation_q': formation_q,
        'status': status,
        'event_type': event_type,
        'students': PfmpUser.objects.filter(role_principal='eleve', active=True).order_by('last_name', 'first_name')[:500],
        'companies': Company.objects.exclude(status='inactive').order_by('name')[:500],
        'periods': PfmpPeriod.objects.exclude(status='archived').order_by('-start_date')[:100],
        'formations': Formation.objects.filter(active=True).order_by('code'),
        'assignment_status_choices': StudentAssignment.STATUS,
        'announcement_status_choices': CompanyAnnouncement.STATUS,
        'user': user,
    }
    return render(request, 'pfmp_manager/history.html', context)

'''
    if marker in text:
        text = text.replace(marker, history_code + marker)
    else:
        text += history_code
    views.write_text(text, encoding='utf-8')

# --- Template PFMP historique ---
history = ROOT / 'pfmp-app/pfmp_manager/templates/pfmp_manager/history.html'
history.write_text(r'''{% extends 'pfmp_manager/base.html' %}
{% block content %}
<section class="hero">
  <div>
    <p class="eyebrow">PFMP Manager</p>
    <h1>Historique PFMP</h1>
    <p class="lead">Historique consolidé des affectations, démarches élèves et annonces entreprises. Les professeurs voient l’ensemble ; un élève ne voit que son propre suivi.</p>
  </div>
  <div class="hero-actions">
    <a class="button secondary" href="?{% if request.GET.urlencode %}{{ request.GET.urlencode }}&{% endif %}export=csv">Exporter CSV</a>
  </div>
</section>

<section class="panel">
  <h2>Filtres</h2>
  <form method="get" class="grid2">
    <label>Recherche libre
      <input type="search" name="q" value="{{ q }}" placeholder="nom, entreprise, commentaire, période...">
    </label>
    <label>Type d’événement
      <select name="event_type">
        <option value="all" {% if event_type == 'all' %}selected{% endif %}>Tout</option>
        <option value="assignment" {% if event_type == 'assignment' %}selected{% endif %}>Affectations</option>
        <option value="step" {% if event_type == 'step' %}selected{% endif %}>Démarches</option>
        <option value="announcement" {% if event_type == 'announcement' %}selected{% endif %}>Annonces</option>
      </select>
    </label>
    <label>Élève
      <input type="search" name="student" value="{{ student_q }}" list="students-list" placeholder="code, nom, prénom">
      <datalist id="students-list">{% for s in students %}<option value="{{ s.code }}">{{ s.full_name }} — {{ s.class_name }}</option>{% endfor %}</datalist>
    </label>
    <label>Entreprise
      <input type="search" name="company" value="{{ company_q }}" list="companies-list" placeholder="nom ou ville">
      <datalist id="companies-list">{% for c in companies %}<option value="{{ c.name }}">{{ c.city }}</option>{% endfor %}</datalist>
    </label>
    <label>Période
      <input type="search" name="period" value="{{ period_q }}" list="periods-list" placeholder="titre période">
      <datalist id="periods-list">{% for p in periods %}<option value="{{ p.title }}">{{ p.start_date }} → {{ p.end_date }}</option>{% endfor %}</datalist>
    </label>
    <label>Formation
      <input type="search" name="formation" value="{{ formation_q }}" list="formations-list" placeholder="MELEC, CIEL, BTS...">
      <datalist id="formations-list">{% for f in formations %}<option value="{{ f.code }}">{{ f.nom }}</option>{% endfor %}</datalist>
    </label>
    <label>Statut
      <select name="status">
        <option value="">Tous statuts</option>
        <optgroup label="Affectations">
          {% for value,label in assignment_status_choices %}<option value="{{ value }}" {% if status == value %}selected{% endif %}>{{ label }}</option>{% endfor %}
        </optgroup>
        <optgroup label="Annonces">
          {% for value,label in announcement_status_choices %}<option value="{{ value }}" {% if status == value %}selected{% endif %}>{{ label }}</option>{% endfor %}
        </optgroup>
      </select>
    </label>
    <div class="actions-row"><button type="submit">Filtrer</button><a class="button secondary" href="{% url 'pfmp_history' %}">Réinitialiser</a></div>
  </form>
</section>

<section class="panel">
  <h2>Événements</h2>
  <table>
    <thead><tr><th>Date</th><th>Type</th><th>Élément</th><th>Contexte</th><th>Statut</th><th>Détail</th></tr></thead>
    <tbody>
      {% for event in events %}
        <tr>
          <td>{{ event.date }}</td>
          <td><span class="badge">{{ event.type }}</span></td>
          <td><strong>{{ event.title }}</strong></td>
          <td>{{ event.subtitle }}</td>
          <td>{{ event.status }}</td>
          <td>{{ event.detail|truncatechars:180 }}</td>
        </tr>
      {% empty %}
        <tr><td colspan="6" class="muted">Aucun événement ne correspond aux filtres.</td></tr>
      {% endfor %}
    </tbody>
  </table>
</section>
{% endblock %}
''', encoding='utf-8')

# --- Documentation release ---
doc = ROOT / 'docs/RELEASE_V0_0_1_RC13.md'
doc.parent.mkdir(parents=True, exist_ok=True)
doc.write_text('''# LP Gestion Atelier EP Suite — V0.0.1-RC13\n\n## Objet\n\nRC13 réintroduit l’historique PFMP Manager demandé : page `/pfmp/historique/`, lien de menu, filtres dynamiques avec suggestions et export CSV.\n\n## Contenu\n\n- Historique consolidé des affectations PFMP.\n- Historique des démarches élèves.\n- Historique des annonces entreprises.\n- Filtres : recherche libre, élève, entreprise, période, formation, statut, type d’événement.\n- Droits : professeur/admin voient tout ; élève voit uniquement son propre historique.\n- Export CSV.\n\n## Déploiement\n\nUpgrade semi-rapide conseillé :\n\n```bash\nlp-suite upgrade rc\n```\n''', encoding='utf-8')
PY

# Recalcul des checksums si l'outil existe.
if [[ -x scripts/create_checksums.sh ]]; then
  bash scripts/create_checksums.sh
elif [[ -f scripts/create_checksums.sh ]]; then
  bash scripts/create_checksums.sh
else
  find . -type f \
    ! -path './.git/*' \
    ! -path './postgres-db/data/*' \
    ! -path './lp-core-db/data/*' \
    ! -path './toolmag-db/data/*' \
    ! -path './safety-db/data/*' \
    ! -path './pedashop-db/data/*' \
    ! -path './system-manager-db/data/*' \
    ! -path './tpmanager-db/data/*' \
    ! -path './pfmp-db/data/*' \
    ! -path './backups/*' \
    -print0 | sort -z | xargs -0 sha256sum > CHECKSUMS.sha256
fi

echo "Patch RC13 PFMP historique appliqué."
echo "Contrôles conseillés :"
echo "  cat VERSION VERSION.txt"
echo "  grep -R \"pfmp_history\|history_view\" -n pfmp-app/pfmp_manager"
echo "  sha256sum -c CHECKSUMS.sha256 | grep -E 'FAILED|WARNING|No such file|did NOT match' || echo CHECKSUMS_OK"
