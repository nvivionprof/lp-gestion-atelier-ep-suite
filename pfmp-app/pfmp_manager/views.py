from django.conf import settings
from django.contrib import messages
from django.core import signing
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from urllib.parse import quote
from django.utils.http import url_has_allowed_host_and_scheme
from .context_processors import current_pfmp_user
from .forms import CompanyForm, CompanyContactForm, PeriodForm, AssignmentForm, StepForm, AnnouncementForm
from .models import Company, CompanyContact, PfmpPeriod, StudentAssignment, StudentStep, CompanyAnnouncement, PfmpUser, Formation
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
    # Change la clé de session à chaque connexion pour éviter de réutiliser une ancienne session/cookie.
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

def dashboard(request):
    user=current_pfmp_user(request)
    periods=PfmpPeriod.objects.exclude(status='archived').order_by('-start_date')[:6]
    assignments=StudentAssignment.objects.select_related('student','period','company').order_by('-updated_at')[:10]
    ctx={'company_count':Company.objects.exclude(status='inactive').count(),'period_count':PfmpPeriod.objects.exclude(status='archived').count(),'assignment_count':StudentAssignment.objects.count(),'step_count':StudentStep.objects.count(),'periods':periods,'assignments':assignments,'user':user}
    return render(request,'pfmp_manager/dashboard.html',ctx)

def company_list(request):
    user=current_pfmp_user(request); q=(request.GET.get('q') or '').strip(); formation=(request.GET.get('formation') or '').strip()
    companies=Company.objects.exclude(status='inactive').prefetch_related('formations')
    if q: companies=companies.filter(Q(name__icontains=q)|Q(activity__icontains=q)|Q(city__icontains=q))
    if formation: companies=companies.filter(formations__code=formation)
    return render(request,'pfmp_manager/company_list.html',{'companies':companies.distinct().order_by('name')[:500],'q':q,'formation':formation,'formations':Formation.objects.filter(active=True)})

def company_detail(request, pk):
    company=get_object_or_404(Company.objects.prefetch_related('contacts','formations'), pk=pk)
    user=current_pfmp_user(request)
    contacts=company.contacts.filter(active=True)
    if not (user and user.is_prof_like):
        contacts=contacts.filter(visibility='students')
        if user and user.formation_code:
            contacts=contacts.filter(Q(formations__isnull=True)|Q(formations__code=user.formation_code)).distinct()
    return render(request,'pfmp_manager/company_detail.html',{'company':company,'contacts':contacts,'user':user})

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
    return render(request,'pfmp_manager/form.html',{'form':form,'title':'Nouvelle entreprise'})

def contact_create(request, company_pk):
    user=current_pfmp_user(request)
    if not (user and user.is_prof_like): return redirect('pfmp_company_detail', company_pk)
    company=get_object_or_404(Company, pk=company_pk)
    if request.method=='POST':
        form=CompanyContactForm(request.POST)
        if form.is_valid():
            obj=form.save(commit=False); obj.company=company; obj.save(); form.save_m2m(); messages.success(request,'Contact ajouté.'); return redirect('pfmp_company_detail', company.pk)
    else: form=CompanyContactForm()
    return render(request,'pfmp_manager/form.html',{'form':form,'title':f'Nouveau contact — {company.name}'})

def period_list(request):
    return render(request,'pfmp_manager/period_list.html',{'periods':PfmpPeriod.objects.prefetch_related('formations').order_by('-start_date')})

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
    q = (request.GET.get('q') or '').strip()
    formation = (request.GET.get('formation') or '').strip()
    companies = Company.objects.exclude(status='inactive').prefetch_related('formations')
    if q:
        companies = companies.filter(Q(name__icontains=q) | Q(activity__icontains=q) | Q(city__icontains=q) | Q(postal_code__icontains=q))
    if formation:
        companies = companies.filter(formations__code=formation)
    return companies.distinct().order_by('name'), q, formation


def _company_geo_payload(companies):
    payload = []
    for company in companies:
        if company.latitude is None or company.longitude is None:
            continue
        payload.append({
            'id': company.pk,
            'name': company.name,
            'activity': company.activity,
            'address': company.address,
            'postal_code': company.postal_code,
            'city': company.city,
            'lat': float(company.latitude),
            'lng': float(company.longitude),
            'status': company.get_status_display(),
            'detail_url': reverse('pfmp_company_detail', args=[company.pk]),
        })
    return payload


def map_view(request):
    companies, q, formation = _filtered_company_queryset(request)
    companies = list(companies[:1000])
    companies_geo = _company_geo_payload(companies)
    companies_without_coords = [c for c in companies if c.latitude is None or c.longitude is None][:50]
    return render(request, 'pfmp_manager/map.html', {
        'companies': companies,
        'companies_geo': companies_geo,
        'companies_without_coords': companies_without_coords,
        'q': q,
        'formation': formation,
        'formations': Formation.objects.filter(active=True).order_by('code'),
    })


def company_geojson(request):
    companies, _q, _formation = _filtered_company_queryset(request)
    features = []
    for item in _company_geo_payload(companies[:1000]):
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [item['lng'], item['lat']]},
            'properties': {
                'id': item['id'],
                'name': item['name'],
                'activity': item['activity'],
                'address': item['address'],
                'postal_code': item['postal_code'],
                'city': item['city'],
                'status': item['status'],
                'detail_url': item['detail_url'],
            }
        })
    return JsonResponse({'type': 'FeatureCollection', 'features': features})



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
