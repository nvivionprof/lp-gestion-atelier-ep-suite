from io import BytesIO
import math
import os
import tempfile
from django.conf import settings
from django.contrib import messages
from django.core import signing
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from .context_processors import current_pfmp_user
from .forms import (
    CompanyForm, CompanyContactForm, PeriodForm, AssignmentForm, StepForm,
    AnnouncementForm, StudentCompanySearchForm, StudentCompanyActionForm,
    CompanyImportForm
)
from .models import (
    Company, CompanyContact, PfmpPeriod, StudentAssignment, StudentStep,
    CompanyAnnouncement, PfmpUser, Formation, StudentCompanySearch,
    StudentCompanyAction, CompanyTag, ImportBatch
)
from .sync import sync_users_from_lp_core, sync_formations_from_lp_core


def _payload(request):
    try:
        return signing.loads(request.GET.get('token') or '', key=settings.LP_CORE_API_TOKEN, salt='lp-suite-sso', max_age=getattr(settings, 'PFMP_SSO_TOKEN_MAX_AGE', 600))
    except Exception:
        return None


def _safe_next_or_dashboard(request):
    nxt = request.GET.get('next') or request.POST.get('next') or ''
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return nxt
    prefix = getattr(settings, 'APP_URL_PREFIX', '').rstrip('/')
    if nxt.startswith('http://') or nxt.startswith('https://') or nxt.startswith('//'):
        return reverse('pfmp_dashboard')
    if prefix and nxt.startswith(prefix + '/'):
        return nxt
    if nxt.startswith('/'):
        return nxt
    return reverse('pfmp_dashboard')


def _establish_pfmp_session(request, user):
    request.session.cycle_key()
    request.session['pfmp_user_id'] = user.id
    request.session['pfmp_user_code'] = user.code
    request.session['pfmp_auth_source'] = 'lp-core-sso'
    request.session.modified = True


def portal_login(request):
    payload = _payload(request)
    if not payload:
        messages.error(request, 'Connexion LP Core impossible ou expirée. Reconnecte-toi à LP Core puis rouvre PFMP Manager.')
        return redirect('pfmp_login')
    code = (payload.get('code') or '').strip()
    username = (payload.get('username') or '').strip()
    user = PfmpUser.objects.filter(Q(code=code) | Q(username=username), active=True).first()
    if not user:
        messages.error(request, 'Compte LP Core non synchronisé dans PFMP Manager. Lance la synchronisation LP Core → PFMP.')
        return redirect('pfmp_login')
    _establish_pfmp_session(request, user)
    messages.success(request, f'Connexion PFMP Manager via LP Core : {user.full_name}.')
    return redirect(_safe_next_or_dashboard(request))


def login_view(request):
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        user = PfmpUser.objects.filter(Q(username=username) | Q(code=username), active=True).first()
        if user and user.check_password(password):
            _establish_pfmp_session(request, user)
            request.session['pfmp_auth_source'] = 'local-login'
            messages.success(request, f'Connexion PFMP Manager : {user.full_name}.')
            return redirect(_safe_next_or_dashboard(request))
        messages.error(request, 'Identifiant ou mot de passe incorrect.')
    return render(request, 'pfmp_manager/login.html')


def logout_view(request):
    request.session.pop('pfmp_user_id', None)
    request.session.pop('pfmp_user_code', None)
    request.session.pop('pfmp_auth_source', None)
    request.session.modified = True
    messages.success(request, 'Déconnexion PFMP Manager effectuée.')
    return redirect('pfmp_login')


def _require_login(request):
    user = current_pfmp_user(request)
    if not user:
        return None, redirect('pfmp_login')
    return user, None


def _student_contact_queryset(company, user):
    qs = company.contacts.filter(active=True)
    if user and not user.is_prof_like:
        qs = qs.filter(student_visible=True)
        if user.formation_code:
            qs = qs.filter(Q(formations__isnull=True) | Q(formations__code=user.formation_code)).distinct()
    return qs




AGREEMENT_SEARCH_STATUSES = {
    'accord_oral', 'accord_mail', 'convention_a_preparer',
    'convention_envoyee', 'convention_signee', 'stage_valide'
}
AGREEMENT_ASSIGNMENT_STATUSES = {'validated', 'convention', 'in_progress', 'completed'}


def _period_class_list(period):
    raw = period.class_names or ''
    return [c.strip() for c in raw.replace(',', ';').split(';') if c.strip()]


def _students_for_period(period):
    students = PfmpUser.objects.filter(active=True, role_principal='eleve').order_by('class_name', 'last_name', 'first_name', 'username')
    classes = _period_class_list(period)
    if classes:
        students = students.filter(class_name__in=classes)
    else:
        formation_codes = list(period.formations.values_list('code', flat=True))
        if formation_codes:
            students = students.filter(formation_code__in=formation_codes)
    return students

def dashboard(request):
    user=current_pfmp_user(request)
    periods=PfmpPeriod.objects.exclude(status='archived').order_by('-start_date')[:6]
    assignments=StudentAssignment.objects.select_related('student','period','company').order_by('-updated_at')[:10]
    searches=StudentCompanySearch.objects.select_related('student','period','company').order_by('-updated_at')[:10]
    if user and not user.is_prof_like:
        assignments=assignments.filter(student=user)
        searches=searches.filter(student=user)
    ctx={
        'company_count':Company.objects.exclude(status='inactive').count(),
        'period_count':PfmpPeriod.objects.exclude(status='archived').count(),
        'assignment_count':StudentAssignment.objects.count(),
        'search_count':StudentCompanySearch.objects.count(),
        'step_count':StudentStep.objects.count()+StudentCompanyAction.objects.count(),
        'periods':periods,'assignments':assignments,'searches':searches,'user':user
    }
    return render(request,'pfmp_manager/dashboard.html',ctx)


def company_list(request):
    user=current_pfmp_user(request)
    q=(request.GET.get('q') or '').strip()
    formation=(request.GET.get('formation') or '').strip()
    status=(request.GET.get('status') or '').strip()
    tag=(request.GET.get('tag') or '').strip()
    companies=Company.objects.exclude(status='inactive').prefetch_related('formations','tags')
    if not (user and user.is_prof_like):
        companies=companies.filter(student_visible=True)
    if q:
        companies=companies.filter(Q(name__icontains=q)|Q(activity__icontains=q)|Q(city__icontains=q)|Q(postal_code__icontains=q)|Q(tags__label__icontains=q)|Q(domains_text__icontains=q)|Q(subdomains_text__icontains=q))
    if formation:
        companies=companies.filter(Q(formations__code=formation)|Q(domains_text__icontains=formation))
    if status:
        companies=companies.filter(status=status)
    if tag:
        companies=companies.filter(tags__code=tag)
    return render(request,'pfmp_manager/company_list.html',{
        'companies':companies.distinct().order_by('name')[:500], 'q':q, 'formation':formation, 'status':status, 'tag':tag,
        'formations':Formation.objects.filter(active=True).order_by('code'),
        'tags':CompanyTag.objects.filter(active=True).order_by('label'),
        'status_choices':Company.STATUS_CHOICES,
        'user':user,
    })


def company_detail(request, pk):
    company=get_object_or_404(Company.objects.prefetch_related('contacts','formations','tags'), pk=pk)
    user=current_pfmp_user(request)
    if not (user and user.is_prof_like) and not company.student_visible:
        messages.error(request, 'Cette entreprise n’est pas visible pour les élèves.')
        return redirect('pfmp_company_list')
    contacts=_student_contact_queryset(company, user)
    searches=StudentCompanySearch.objects.filter(company=company).select_related('student','period','contact').order_by('-updated_at')[:50]
    if user and not user.is_prof_like:
        searches=searches.filter(student=user)
    return render(request,'pfmp_manager/company_detail.html',{'company':company,'contacts':contacts,'user':user,'searches':searches})


def company_create(request):
    user=current_pfmp_user(request)
    if not user: return redirect('pfmp_login')
    if request.method=='POST':
        form=CompanyForm(request.POST)
        if form.is_valid():
            obj=form.save(commit=False); obj.created_by=user
            if not user.is_prof_like: obj.status='provisoire'
            obj.save(); form.save_m2m(); messages.success(request,'Entreprise enregistrée.'); return redirect('pfmp_company_detail', obj.pk)
    else: form=CompanyForm()
    return render(request,'pfmp_manager/form.html',{'form':form,'title':'Nouvelle entreprise','submit_label':'Enregistrer l’entreprise'})


def company_update(request, pk):
    user, response = _require_login(request)
    if response: return response
    if not user.is_prof_like:
        messages.error(request, 'Modification réservée aux professeurs ou administrateurs PFMP.')
        return redirect('pfmp_company_detail', pk)
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entreprise modifiée.')
            return redirect('pfmp_company_detail', company.pk)
    else:
        form = CompanyForm(instance=company)
    return render(request, 'pfmp_manager/form.html', {'form': form, 'title': f'Modifier l’entreprise — {company.name}', 'submit_label': 'Enregistrer les modifications'})


def contact_create(request, company_pk):
    user=current_pfmp_user(request)
    if not (user and user.is_prof_like): return redirect('pfmp_company_detail', company_pk)
    company=get_object_or_404(Company, pk=company_pk)
    if request.method=='POST':
        form=CompanyContactForm(request.POST)
        if form.is_valid():
            obj=form.save(commit=False); obj.company=company; obj.save(); form.save_m2m(); messages.success(request,'Contact ajouté.'); return redirect('pfmp_company_detail', company.pk)
    else: form=CompanyContactForm()
    return render(request,'pfmp_manager/form.html',{'form':form,'title':f'Nouveau contact — {company.name}','submit_label':'Enregistrer le contact'})


def contact_update(request, company_pk, contact_pk):
    user, response = _require_login(request)
    if response: return response
    if not user.is_prof_like:
        messages.error(request, 'Modification des contacts réservée aux professeurs ou administrateurs PFMP.')
        return redirect('pfmp_company_detail', company_pk)
    company = get_object_or_404(Company, pk=company_pk)
    contact = get_object_or_404(CompanyContact, pk=contact_pk, company=company)
    if request.method == 'POST':
        form = CompanyContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contact modifié.')
            return redirect('pfmp_company_detail', company.pk)
    else:
        form = CompanyContactForm(instance=contact)
    return render(request, 'pfmp_manager/form.html', {'form': form, 'title': f'Modifier le contact — {contact.full_name}', 'submit_label': 'Enregistrer le contact'})


def period_list(request):
    periods = PfmpPeriod.objects.prefetch_related('formations').order_by('-start_date')
    return render(request,'pfmp_manager/period_list.html',{'periods':periods})


def period_summary(request, period_pk):
    user, response = _require_login(request)
    if response: return response
    if not user.is_prof_like:
        messages.error(request, 'Bilan de période réservé aux professeurs ou administrateurs PFMP.')
        return redirect('pfmp_period_list')
    period = get_object_or_404(PfmpPeriod.objects.prefetch_related('formations'), pk=period_pk)
    students = list(_students_for_period(period))
    rows = []
    class_stats = {}
    total_searches = 0
    total_with_agreement = 0
    total_without_agreement = 0
    for student in students:
        searches = list(StudentCompanySearch.objects.filter(student=student, period=period).select_related('company','contact').prefetch_related('actions').order_by('company__name'))
        search_count = len({s.company_id for s in searches})
        agreement_searches = [s for s in searches if s.status in AGREEMENT_SEARCH_STATUSES]
        assignment = StudentAssignment.objects.filter(student=student, period=period).select_related('company').first()
        assignment_ok = bool(assignment and assignment.status in AGREEMENT_ASSIGNMENT_STATUSES)
        has_agreement = bool(agreement_searches or assignment_ok)
        total_searches += search_count
        if has_agreement:
            total_with_agreement += 1
        else:
            total_without_agreement += 1
        cls = student.class_name or 'Classe non renseignée'
        class_stats.setdefault(cls, {'class_name': cls, 'students': 0, 'with_agreement': 0, 'without_agreement': 0, 'search_count': 0})
        class_stats[cls]['students'] += 1
        class_stats[cls]['search_count'] += search_count
        if has_agreement:
            class_stats[cls]['with_agreement'] += 1
        else:
            class_stats[cls]['without_agreement'] += 1
        rows.append({
            'student': student,
            'search_count': search_count,
            'has_agreement': has_agreement,
            'agreement_searches': agreement_searches,
            'assignment': assignment,
            'searches': searches,
            'last_action': max([a.created_at for s in searches for a in list(s.actions.all())], default=None),
        })
    rows.sort(key=lambda r: (r['student'].class_name or '', not r['has_agreement'], r['student'].last_name or '', r['student'].first_name or ''))
    return render(request, 'pfmp_manager/period_summary.html', {
        'period': period,
        'classes': _period_class_list(period),
        'rows': rows,
        'class_stats': sorted(class_stats.values(), key=lambda x: x['class_name']),
        'total_students': len(students),
        'total_searches': total_searches,
        'total_with_agreement': total_with_agreement,
        'total_without_agreement': total_without_agreement,
        'agreement_statuses': AGREEMENT_SEARCH_STATUSES,
    })


def period_create(request):
    user=current_pfmp_user(request)
    if not (user and user.is_prof_like): return redirect('pfmp_period_list')
    if request.method=='POST':
        form=PeriodForm(request.POST)
        if form.is_valid(): obj=form.save(); messages.success(request,'Période PFMP créée.'); return redirect('pfmp_period_list')
    else: form=PeriodForm()
    return render(request,'pfmp_manager/form.html',{'form':form,'title':'Nouvelle période PFMP'})


def assignment_list(request):
    user=current_pfmp_user(request)
    qs=StudentAssignment.objects.select_related('student','period','company','teacher').order_by('-updated_at')
    if user and not user.is_prof_like: qs=qs.filter(student=user)
    return render(request,'pfmp_manager/assignment_list.html',{'assignments':qs[:500]})


def assignment_create(request):
    user=current_pfmp_user(request)
    if not (user and user.is_prof_like): return redirect('pfmp_assignment_list')
    if request.method=='POST':
        form=AssignmentForm(request.POST)
        if form.is_valid(): obj=form.save(); messages.success(request,'Affectation enregistrée.'); return redirect('pfmp_assignment_list')
    else: form=AssignmentForm()
    return render(request,'pfmp_manager/form.html',{'form':form,'title':'Nouvelle affectation PFMP'})


def step_create(request, assignment_pk):
    user=current_pfmp_user(request)
    assignment=get_object_or_404(StudentAssignment, pk=assignment_pk)
    if not user or (not user.is_prof_like and assignment.student_id != user.id): return redirect('pfmp_assignment_list')
    if request.method=='POST':
        form=StepForm(request.POST)
        if form.is_valid(): obj=form.save(commit=False); obj.assignment=assignment; obj.created_by=user; obj.save(); messages.success(request,'Démarche ajoutée.'); return redirect('pfmp_assignment_list')
    else: form=StepForm()
    return render(request,'pfmp_manager/form.html',{'form':form,'title':'Ajouter une démarche'})


def _filtered_company_queryset(request):
    user=current_pfmp_user(request)
    q = (request.GET.get('q') or '').strip()
    formation = (request.GET.get('formation') or '').strip()
    tag = (request.GET.get('tag') or '').strip()
    companies = Company.objects.exclude(status='inactive').prefetch_related('formations','tags','contacts')
    if not (user and user.is_prof_like):
        companies = companies.filter(student_visible=True)
    if q:
        companies = companies.filter(Q(name__icontains=q) | Q(activity__icontains=q) | Q(city__icontains=q) | Q(postal_code__icontains=q) | Q(tags__label__icontains=q) | Q(domains_text__icontains=q) | Q(subdomains_text__icontains=q))
    if formation:
        companies = companies.filter(Q(formations__code=formation) | Q(domains_text__icontains=formation))
    if tag:
        companies = companies.filter(tags__code=tag)
    return companies.distinct().order_by('name'), q, formation, tag


def _company_geo_payload(companies, user=None):
    payload = []
    for company in companies:
        lat = company.latitude
        lng = company.longitude
        source = 'entreprise'
        proximity_label = ''
        if lat is None or lng is None:
            contact = company.contacts.filter(active=True, use_personal_location_for_student_search=True, personal_latitude__isnull=False, personal_longitude__isnull=False).first()
            if contact:
                lat, lng = contact.personal_latitude, contact.personal_longitude
                source = 'contact_proximite'
                proximity_label = 'Point de proximité contact — adresse masquée'
        if lat is None or lng is None:
            continue
        payload.append({
            'id': company.pk,
            'name': company.name,
            'activity': company.activity,
            'address': company.address if source == 'entreprise' else '',
            'postal_code': company.postal_code if source == 'entreprise' else '',
            'city': company.city if source == 'entreprise' else '',
            'lat': float(lat),
            'lng': float(lng),
            'status': company.get_status_display(),
            'source': source,
            'proximity_label': proximity_label,
            'detail_url': reverse('pfmp_company_detail', args=[company.pk]),
            'add_url': reverse('pfmp_search_add_company', args=[company.pk]),
        })
    return payload


def map_view(request):
    companies, q, formation, tag = _filtered_company_queryset(request)
    companies = list(companies[:1000])
    companies_geo = _company_geo_payload(companies, current_pfmp_user(request))
    companies_without_coords = [c for c in companies if c.latitude is None or c.longitude is None][:50]
    return render(request, 'pfmp_manager/map.html', {
        'companies': companies,
        'companies_geo': companies_geo,
        'companies_without_coords': companies_without_coords,
        'q': q,
        'formation': formation,
        'tag': tag,
        'formations': Formation.objects.filter(active=True).order_by('code'),
        'tags': CompanyTag.objects.filter(active=True).order_by('label'),
    })


def company_geojson(request):
    companies, _q, _formation, _tag = _filtered_company_queryset(request)
    features = []
    for item in _company_geo_payload(companies[:1000], current_pfmp_user(request)):
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [item['lng'], item['lat']]},
            'properties': item,
        })
    return JsonResponse({'type': 'FeatureCollection', 'features': features})


def my_searches(request):
    user, response = _require_login(request)
    if response: return response
    period = request.GET.get('period') or ''
    status = request.GET.get('status') or ''
    action_type = request.GET.get('action_type') or ''
    qs = StudentCompanySearch.objects.select_related('student','period','company','contact').prefetch_related('actions')
    if not user.is_prof_like:
        qs = qs.filter(student=user)
    else:
        student = request.GET.get('student') or ''
        class_name = request.GET.get('class_name') or ''
        if student:
            qs = qs.filter(Q(student__code__icontains=student)|Q(student__username__icontains=student)|Q(student__last_name__icontains=student))
        if class_name:
            qs = qs.filter(student__class_name__icontains=class_name)
    if period:
        qs = qs.filter(period_id=period)
    if status:
        qs = qs.filter(status=status)
    if action_type:
        qs = qs.filter(actions__action_type=action_type)
    searches = list(qs.distinct().order_by('-updated_at')[:800])
    for s in searches:
        actions = list(s.actions.all())
        s.latest_action = actions[0] if actions else None
    return render(request, 'pfmp_manager/my_searches.html', {
        'searches': searches,
        'periods': PfmpPeriod.objects.exclude(status='archived').order_by('-start_date'),
        'status_choices': StudentCompanySearch.STATUS,
        'action_choices': StudentCompanyAction.ACTION,
        'user': user,
        'filters': request.GET,
    })


def search_add_company(request, company_pk):
    user, response = _require_login(request)
    if response: return response
    company = get_object_or_404(Company, pk=company_pk)
    if not user.is_prof_like and not company.student_visible:
        messages.error(request, 'Entreprise non visible pour les élèves.')
        return redirect('pfmp_company_list')
    if request.method == 'POST':
        form = StudentCompanySearchForm(request.POST, company=company, user=user)
        if form.is_valid():
            search, created = StudentCompanySearch.objects.get_or_create(
                student=user if not user.is_prof_like else user,
                period=form.cleaned_data['period'],
                company=company,
                defaults={
                    'contact': form.cleaned_data.get('contact'),
                    'tags_text': form.cleaned_data.get('tags_text',''),
                    'created_by': user,
                    'status': 'recherche',
                }
            )
            if not created:
                search.contact = form.cleaned_data.get('contact') or search.contact
                search.tags_text = form.cleaned_data.get('tags_text') or search.tags_text
                search.save()
            action_type = form.cleaned_data['first_action_type']
            status_map = {'mail':'mail_envoye','telephone':'appel_effectue','visite':'recherche','depot_cv':'demande_envoyee'}
            StudentCompanyAction.objects.create(
                search=search,
                created_by=user,
                action_type=action_type,
                contact=form.cleaned_data.get('contact'),
                comment=form.cleaned_data.get('first_comment',''),
                status_after=status_map.get(action_type, 'recherche'),
                next_action=form.cleaned_data.get('first_next_action',''),
                next_action_date=form.cleaned_data.get('first_next_action_date'),
            )
            messages.success(request, 'Entreprise ajoutée à ta recherche PFMP.')
            return redirect('pfmp_search_detail', search.pk)
    else:
        form = StudentCompanySearchForm(company=company, user=user)
    return render(request, 'pfmp_manager/search_form.html', {'form': form, 'company': company, 'title': 'Ajouter à ma recherche'})


def search_detail(request, search_pk):
    user, response = _require_login(request)
    if response: return response
    search = get_object_or_404(StudentCompanySearch.objects.select_related('student','period','company','contact'), pk=search_pk)
    if not user.is_prof_like and search.student_id != user.id:
        messages.error(request, 'Accès interdit à cette recherche.')
        return redirect('pfmp_my_searches')
    return render(request, 'pfmp_manager/search_detail.html', {'search': search, 'actions': search.actions.select_related('contact','created_by').all(), 'user': user})


def search_action_create(request, search_pk):
    user, response = _require_login(request)
    if response: return response
    search = get_object_or_404(StudentCompanySearch.objects.select_related('student','company'), pk=search_pk)
    if not user.is_prof_like and search.student_id != user.id:
        messages.error(request, 'Accès interdit à cette recherche.')
        return redirect('pfmp_my_searches')
    if request.method == 'POST':
        form = StudentCompanyActionForm(request.POST, request.FILES, search=search, user=user)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.search = search
            obj.created_by = user
            obj.save()
            messages.success(request, 'Action horodatée ajoutée.')
            return redirect('pfmp_search_detail', search.pk)
    else:
        form = StudentCompanyActionForm(search=search, user=user)
    return render(request, 'pfmp_manager/form.html', {'form': form, 'title': 'Ajouter une action de recherche'})


def search_pdf(request):
    user, response = _require_login(request)
    if response: return response
    period_id = request.GET.get('period') or None
    qs = StudentCompanySearch.objects.select_related('student','period','company','contact').prefetch_related('actions')
    if not user.is_prof_like:
        qs = qs.filter(student=user)
    if period_id:
        qs = qs.filter(period_id=period_id)
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    width, height = landscape(A4)
    y = height - 1.5*cm
    c.setFont('Helvetica-Bold', 14)
    c.drawString(1.2*cm, y, 'PFMP Manager — Tableau récapitulatif des recherches')
    y -= 0.7*cm
    c.setFont('Helvetica', 9)
    c.drawString(1.2*cm, y, f'Généré le {timezone.localtime().strftime("%d/%m/%Y %H:%M")} — utilisateur : {user.full_name}')
    y -= 0.8*cm
    headers = ['Élève', 'Période', 'Entreprise', 'Contact mail', 'État', 'Dernière action']
    xs = [1.2, 5.5, 9.5, 15.0, 20.0, 23.5]
    c.setFont('Helvetica-Bold', 8)
    for x, h in zip(xs, headers): c.drawString(x*cm, y, h)
    y -= 0.4*cm
    c.setFont('Helvetica', 7)
    for s in qs.order_by('student__last_name','period__start_date','company__name')[:350]:
        if y < 1.5*cm:
            c.showPage(); y = height - 1.5*cm; c.setFont('Helvetica', 7)
        last = s.actions.first()
        vals = [s.student.full_name[:28], s.period.title[:28], s.company.name[:35], (s.contact.email if s.contact else '')[:28], s.get_status_display()[:22], (last.created_at.strftime('%d/%m/%Y') + ' ' + last.get_action_type_display() if last else '')[:32]]
        for x, v in zip(xs, vals): c.drawString(x*cm, y, v)
        y -= 0.35*cm
    c.save()
    pdf = buf.getvalue(); buf.close()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="recherches_pfmp.pdf"'
    return response


def import_companies(request):
    user=current_pfmp_user(request)
    if not (user and user.is_prof_like):
        messages.error(request, 'Import réservé aux professeurs ou administrateurs PFMP.')
        return redirect('pfmp_company_list')
    report = None
    if request.method == 'POST':
        form = CompanyImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = form.cleaned_data['file']
            mode = form.cleaned_data['mode']
            key = form.cleaned_data['key']
            confirm = form.cleaned_data.get('confirm') or ''
            fd, tmp = tempfile.mkstemp(suffix='.xlsx')
            os.close(fd)
            with open(tmp, 'wb') as f:
                for chunk in uploaded.chunks(): f.write(chunk)
            try:
                from django.core.management import call_command
                out = BytesIO()
                # call_command stdout expects text; use simple report through return object by DB ImportBatch after command.
                call_command('import_pfmp_companies_xlsx', file=tmp, mode=mode, key=key, confirm=confirm, stdout=None)
                report = ImportBatch.objects.order_by('-started_at').first()
                messages.success(request, 'Import PFMP terminé. Consulte le rapport ci-dessous.')
            except Exception as exc:
                messages.error(request, f'Import en erreur : {exc}')
            finally:
                try: os.remove(tmp)
                except OSError: pass
    else:
        form = CompanyImportForm()
    return render(request, 'pfmp_manager/import_companies.html', {'form': form, 'report': report})


def announcement_list(request):
    return render(request,'pfmp_manager/announcement_list.html',{'announcements':CompanyAnnouncement.objects.select_related('company').order_by('-created_at')[:200]})


def announcement_create(request):
    user=current_pfmp_user(request)
    if not (user and user.is_prof_like): return redirect('pfmp_announcement_list')
    if request.method=='POST':
        form=AnnouncementForm(request.POST)
        if form.is_valid(): obj=form.save(); messages.success(request,'Annonce enregistrée.'); return redirect('pfmp_announcement_list')
    else: form=AnnouncementForm()
    return render(request,'pfmp_manager/form.html',{'form':form,'title':'Nouvelle annonce entreprise — socle V2'})


def help_view(request): return render(request,'pfmp_manager/help.html')
def about_view(request): return render(request,'pfmp_manager/about.html')
def api_health(request): return JsonResponse({'ok':True,'module':'pfmp','version':settings.PFMP_VERSION})


@csrf_exempt
@require_http_methods(['POST'])
def sync_lp_core_view(request):
    token=request.headers.get('X-API-Key') or request.POST.get('token')
    if settings.LP_CORE_API_TOKEN and token != settings.LP_CORE_API_TOKEN:
        return JsonResponse({'ok':False,'error':'forbidden'}, status=403)
    force=request.POST.get('force_password')=='1'; core_user_id=request.POST.get('core_user_id') or None
    users=sync_users_from_lp_core(force_password=force, core_user_id=core_user_id)
    formations=sync_formations_from_lp_core()
    return JsonResponse({'ok':not users['errors'] and not formations['errors'], 'users':users, 'formations':formations})
