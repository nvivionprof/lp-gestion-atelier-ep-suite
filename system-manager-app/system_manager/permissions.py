from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from .models import SystemUser, TemporarySystemPermission


def current_system_user(request):
    uid = request.session.get('system_user_id')
    if not uid:
        return None
    return SystemUser.objects.filter(id=uid, active=True).first()


def _active_temporary_permissions(user):
    if not user:
        return TemporarySystemPermission.objects.none()
    now = timezone.now()
    qs = TemporarySystemPermission.objects.filter(active=True, date_debut__lte=now, date_fin__gte=now)
    class_name = (user.class_name or '').strip()
    return qs.filter(user=user) | qs.filter(school_class__nom=class_name)


def can_create_systems(user):
    return bool(user and (user.is_prof_like or _active_temporary_permissions(user).filter(can_create=True).exists()))


def can_edit_systems(user, systeme=None):
    if not user:
        return False
    if user.is_prof_like:
        return True
    perms = _active_temporary_permissions(user).filter(can_edit=True)
    if systeme is None:
        return perms.exists()
    for perm in perms:
        if perm.allows_system(systeme, create=False):
            return True
    return False


def system_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = current_system_user(request)
        if not user:
            messages.error(request, 'Connexion System Manager requise.')
            return redirect('system_login')
        request.system_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def system_edit_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = current_system_user(request)
        if not user or not (user.is_prof_like or can_create_systems(user) or can_edit_systems(user)):
            messages.error(request, 'Accès réservé aux professeurs, responsables, administrateurs ou droits temporaires actifs.')
            return redirect('system_dashboard')
        request.system_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def system_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = current_system_user(request)
        if not user or not user.is_admin_like:
            messages.error(request, 'Accès réservé aux administrateurs System Manager.')
            return redirect('system_dashboard')
        request.system_user = user
        return view_func(request, *args, **kwargs)
    return wrapper
