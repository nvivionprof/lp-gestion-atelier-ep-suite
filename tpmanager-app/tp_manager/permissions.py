from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from .context_processors import current_tp_user


def tp_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not current_tp_user(request):
            messages.error(request, 'Connexion TP Manager nécessaire.')
            return redirect('tp_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def tp_prof_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = current_tp_user(request)
        if not user:
            messages.error(request, 'Connexion TP Manager nécessaire.')
            return redirect('tp_login')
        if not user.is_prof_like:
            messages.error(request, 'Accès réservé aux professeurs ou administrateurs.')
            return redirect('tp_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def tp_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = current_tp_user(request)
        if not user:
            messages.error(request, 'Connexion TP Manager nécessaire.')
            return redirect('tp_login')
        if not user.is_admin_like:
            messages.error(request, 'Accès réservé aux administrateurs.')
            return redirect('tp_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
