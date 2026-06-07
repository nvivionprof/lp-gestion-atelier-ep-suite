from django.shortcuts import redirect
from .context_processors import current_pfmp_user

def pfmp_login_required(view):
    def wrapper(request,*args,**kwargs):
        if not current_pfmp_user(request): return redirect('pfmp_login')
        return view(request,*args,**kwargs)
    return wrapper

def pfmp_prof_required(view):
    def wrapper(request,*args,**kwargs):
        user=current_pfmp_user(request)
        if not user: return redirect('pfmp_login')
        if not user.is_prof_like: return redirect('pfmp_dashboard')
        return view(request,*args,**kwargs)
    return wrapper
