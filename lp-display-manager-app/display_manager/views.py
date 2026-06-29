import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import signing
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from .forms import DisplayLayoutForm, DisplayMediaForm, DisplayQRCodeActionForm, DisplayScreenForm, DisplayZoneItemForm
from .models import DisplayCommand, DisplayLayout, DisplayMedia, DisplayQRCodeAction, DisplayScreen, DisplayZoneItem
from .services import build_manifest, execute_qr_action




@require_http_methods(["GET", "POST"])
def local_login(request):
    if request.user.is_authenticated:
        return redirect('display_manager:dashboard')
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return redirect(request.GET.get('next') or 'display_manager:dashboard')
        messages.error(request, 'Identifiant ou mot de passe invalide pour LP Display Manager.')
    return render(request, 'display_manager/login.html')


def local_logout(request):
    logout(request)
    return redirect('display_manager:login')


def portal_login(request):
    token = request.GET.get('token') or ''
    try:
        payload = signing.loads(
            token,
            key=getattr(settings, 'LP_CORE_API_TOKEN', ''),
            salt='lp-suite-sso',
            max_age=600,
        )
    except Exception:
        messages.error(request, 'Jeton LP Core invalide ou expiré. Relance le module depuis le portail LP Core.')
        return redirect('display_manager:login')

    username = (payload.get('username') or payload.get('code') or '').strip()
    code = (payload.get('code') or username).strip()
    role = (payload.get('role') or '').strip().lower()
    if not username:
        messages.error(request, 'Jeton LP Core incomplet : utilisateur absent.')
        return redirect('display_manager:login')

    User = get_user_model()
    user, _ = User.objects.get_or_create(username=username)
    user.is_active = True
    user.is_staff = role in {'admin', 'responsable', 'professeur'}
    user.is_superuser = role in {'admin', 'responsable'}
    if not user.first_name:
        user.first_name = code
    # Mot de passe inutilisable : accès normal par SSO LP Core.
    if not user.has_usable_password():
        user.set_unusable_password()
    user.save()
    login(request, user)
    return redirect('display_manager:dashboard')




def _can_manage_display(user):
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))

def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
def dashboard(request):
    screens = list(DisplayScreen.objects.select_related('active_layout'))
    for screen in screens:
        computed = screen.compute_status()
        if screen.status != computed:
            screen.status = computed
            screen.save(update_fields=['status'])
    context = {
        'screen_count': DisplayScreen.objects.count(),
        'online_count': DisplayScreen.objects.filter(status=DisplayScreen.STATUS_ONLINE).count(),
        'offline_count': DisplayScreen.objects.filter(status=DisplayScreen.STATUS_OFFLINE).count(),
        'layout_count': DisplayLayout.objects.count(),
        'media_count': DisplayMedia.objects.count(),
        'screens': screens[:10],
        'commands': DisplayCommand.objects.select_related('screen')[:10],
    }
    return render(request, 'display_manager/dashboard.html', context)


@login_required
def screens(request):
    return render(request, 'display_manager/screens.html', {
        'screens': DisplayScreen.objects.select_related('active_layout').all(),
    })


@login_required
def screen_create(request):
    if request.method == 'POST':
        form = DisplayScreenForm(request.POST)
        if form.is_valid():
            screen = form.save()
            messages.success(request, 'Écran créé.')
            return redirect('display_manager:screen_detail', pk=screen.pk)
    else:
        form = DisplayScreenForm()
    return render(request, 'display_manager/form.html', {'form': form, 'title': 'Nouvel écran'})


@login_required
def screen_detail(request, pk):
    screen = get_object_or_404(DisplayScreen.objects.select_related('active_layout'), pk=pk)
    return render(request, 'display_manager/screen_detail.html', {
        'screen': screen,
        'commands': screen.commands.all()[:20],
    })


@login_required
def screen_edit(request, pk):
    screen = get_object_or_404(DisplayScreen, pk=pk)
    if request.method == 'POST':
        form = DisplayScreenForm(request.POST, instance=screen)
        if form.is_valid():
            form.save()
            messages.success(request, 'Écran mis à jour.')
            return redirect('display_manager:screen_detail', pk=screen.pk)
    else:
        form = DisplayScreenForm(instance=screen)
    return render(request, 'display_manager/form.html', {'form': form, 'title': f'Modifier {screen.name}'})


@login_required
def layouts(request):
    return render(request, 'display_manager/layouts.html', {
        'layouts': DisplayLayout.objects.prefetch_related('zones__items__media').all(),
    })


@login_required
def layout_create(request):
    if request.method == 'POST':
        form = DisplayLayoutForm(request.POST)
        if form.is_valid():
            layout = form.save()
            layout.ensure_default_zones()
            messages.success(request, 'Layout créé avec ses zones par défaut.')
            return redirect('display_manager:layout_edit', pk=layout.pk)
    else:
        form = DisplayLayoutForm()
    return render(request, 'display_manager/form.html', {'form': form, 'title': 'Nouveau layout'})


@login_required
def layout_duplicate(request, pk):
    layout = get_object_or_404(DisplayLayout, pk=pk)
    copy = layout.duplicate()
    messages.success(request, f'Layout dupliqué : {copy.name}')
    return redirect('display_manager:layout_edit', pk=copy.pk)


@login_required
def layout_edit(request, pk):
    layout = get_object_or_404(DisplayLayout.objects.prefetch_related('zones__items__media'), pk=pk)
    layout.ensure_default_zones()
    if request.method == 'POST':
        form = DisplayZoneItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Élément ajouté à la zone.')
            return redirect('display_manager:layout_edit', pk=layout.pk)
    else:
        form = DisplayZoneItemForm(initial={'duration_seconds': 15})
        form.fields['zone'].queryset = layout.zones.all()
    return render(request, 'display_manager/layout_edit.html', {
        'layout': layout,
        'form': form,
    })


@login_required
def zone_item_delete(request, pk):
    item = get_object_or_404(DisplayZoneItem, pk=pk)
    layout_pk = item.zone.layout.pk
    item.delete()
    messages.success(request, 'Élément supprimé.')
    return redirect('display_manager:layout_edit', pk=layout_pk)


@user_passes_test(_can_manage_display)
def media_library(request):
    if request.method == 'POST':
        form = DisplayMediaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Média ajouté.')
            return redirect('display_manager:media_library')
    else:
        form = DisplayMediaForm()
    return render(request, 'display_manager/media_library.html', {
        'form': form,
        'media_list': DisplayMedia.objects.all(),
    })


@user_passes_test(_can_manage_display)
def media_delete(request, pk):
    media = get_object_or_404(DisplayMedia, pk=pk)
    if request.method != 'POST':
        messages.error(request, 'Suppression refusée : utilise le bouton de suppression de la médiathèque.')
        return redirect('display_manager:media_library')
    name = media.name
    image = media.image
    media.delete()
    if image:
        try:
            image.delete(save=False)
        except Exception:
            pass
    messages.success(request, f'Média supprimé : {name}')
    return redirect('display_manager:media_library')


@login_required
def qr_actions(request):
    if request.method == 'POST':
        form = DisplayQRCodeActionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'QR action créée.')
            return redirect('display_manager:qr_actions')
    else:
        form = DisplayQRCodeActionForm(initial={'duration_seconds': 60, 'target_zone': 'all'})
    return render(request, 'display_manager/qr_actions.html', {
        'form': form,
        'qr_actions': DisplayQRCodeAction.objects.select_related('target_screen').all(),
    })


def player(request, token):
    screen = get_object_or_404(DisplayScreen, player_token=token, is_active=True)
    return render(request, 'display_manager/player.html', {'screen': screen})


@require_GET
def api_manifest(request, token):
    screen = get_object_or_404(DisplayScreen, player_token=token, is_active=True)
    return JsonResponse(build_manifest(screen, request=request))


@csrf_exempt
@require_POST
def api_heartbeat(request, token):
    screen = get_object_or_404(DisplayScreen, player_token=token, is_active=True)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = {}
    screen.touch(ip=_client_ip(request), agent_version=payload.get('agent_version', ''))
    return JsonResponse({'ok': True, 'server_time': timezone.now().isoformat()})


@require_GET
def api_commands(request, token):
    screen = get_object_or_404(DisplayScreen, player_token=token, is_active=True)
    screen.touch(ip=_client_ip(request))
    commands = []
    for command in screen.commands.filter(status=DisplayCommand.STATUS_PENDING).order_by('created_at')[:10]:
        command.status = DisplayCommand.STATUS_SENT
        command.sent_at = timezone.now()
        command.save(update_fields=['status', 'sent_at'])
        commands.append({
            'id': command.id,
            'action': command.action,
            'payload': command.payload,
        })
    return JsonResponse({'commands': commands})


@csrf_exempt
@require_POST
def api_command_result(request, token, command_id):
    screen = get_object_or_404(DisplayScreen, player_token=token, is_active=True)
    command = get_object_or_404(DisplayCommand, pk=command_id, screen=screen)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = {}
    command.status = DisplayCommand.STATUS_DONE if payload.get('ok', True) else DisplayCommand.STATUS_FAILED
    command.result = payload.get('result', '')
    command.executed_at = timezone.now()
    command.save(update_fields=['status', 'result', 'executed_at'])
    return JsonResponse({'ok': True})


def qr_execute(request, token):
    qr_action = get_object_or_404(DisplayQRCodeAction, token=token)
    command = execute_qr_action(qr_action)
    if not command:
        return render(request, 'display_manager/qr_done.html', {
            'ok': False,
            'message': 'QR code inactif ou expiré.',
        }, status=403)
    return render(request, 'display_manager/qr_done.html', {
        'ok': True,
        'message': f'Commande envoyée : {command.get_action_display()} → {command.screen.name}',
        'command': command,
    })


@login_required
def send_command(request, pk, action):
    screen = get_object_or_404(DisplayScreen, pk=pk)
    if action not in [DisplayCommand.ACTION_FREEZE, DisplayCommand.ACTION_RESUME, DisplayCommand.ACTION_RELOAD]:
        raise Http404
    payload = {}
    if action == DisplayCommand.ACTION_FREEZE:
        payload = {'target': 'all', 'duration': 60}
    DisplayCommand.objects.create(screen=screen, action=action, payload=payload)
    messages.success(request, 'Commande créée.')
    return redirect('display_manager:screen_detail', pk=screen.pk)
