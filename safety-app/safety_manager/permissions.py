from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from .models import SafetyUser
from .services import user_is_safety_admin, user_can_edit_safety, user_can_declare_event


def current_safety_user(request):
    uid = request.session.get('safety_user_id')
    if not uid:
        return None
    return SafetyUser.objects.filter(id=uid, active=True).first()


def safety_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not current_safety_user(request):
            messages.error(request, 'Connexion Safety Manager requise.')
            return redirect('safety_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def safety_edit_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = current_safety_user(request)
        if not user_can_edit_safety(user):
            messages.error(request, 'Accès réservé aux professeurs, responsables atelier ou administrateurs.')
            return redirect('safety_dashboard')
        request.safety_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def safety_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = current_safety_user(request)
        if not user_is_safety_admin(user):
            messages.error(request, 'Accès réservé aux administrateurs Safety.')
            return redirect('safety_dashboard')
        request.safety_user = user
        return view_func(request, *args, **kwargs)
    return wrapper


def safety_declare_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = current_safety_user(request)
        if not user_can_declare_event(user):
            messages.error(request, 'Vous n’avez pas les droits pour déclarer un événement.')
            return redirect('safety_dashboard')
        request.safety_user = user
        return view_func(request, *args, **kwargs)
    return wrapper
