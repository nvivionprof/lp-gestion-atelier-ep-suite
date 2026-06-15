from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from .forms import TLSConfigForm, ManualCertificateUploadForm
from .models import TLSConfig, TLSOperationLog
from .services import tls_status, duckdns_issue, duckdns_renew


def _remote_ip(request):
    return request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")).split(",")[0]


def _log(request, action, success, output):
    TLSOperationLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        success=success,
        output=output[-6000:],
        remote_ip=_remote_ip(request) or None,
    )


@login_required
@permission_required("lp_core_tls_manager.core_tls_view", raise_exception=True)
def tls_dashboard(request):
    cfg = TLSConfig.get_solo()
    status_ok, status_output = tls_status()
    logs = TLSOperationLog.objects.all()[:20]
    return render(request, "lp_core/tls_manager/dashboard.html", {
        "cfg": cfg,
        "config_form": TLSConfigForm(instance=cfg),
        "manual_form": ManualCertificateUploadForm(),
        "status_ok": status_ok,
        "status_output": status_output,
        "logs": logs,
    })


@login_required
@permission_required("lp_core_tls_manager.core_tls_run_operations", raise_exception=True)
def tls_save_config(request):
    cfg = TLSConfig.get_solo()
    form = TLSConfigForm(request.POST, instance=cfg)
    if form.is_valid():
        form.save()
        messages.success(request, "Configuration TLS enregistrée.")
    else:
        messages.error(request, "Configuration TLS invalide.")
    return redirect("lp_core_tls_dashboard")


@login_required
@permission_required("lp_core_tls_manager.core_tls_manage_duckdns", raise_exception=True)
def tls_duckdns_issue(request):
    cfg = TLSConfig.get_solo()
    token = request.POST.get("duckdns_token", "")
    ok, output = duckdns_issue(token, cfg)
    _log(request, "duckdns-issue", ok, output)
    messages.success(request, "Certificat DuckDNS généré.") if ok else messages.error(request, "Échec génération DuckDNS.")
    return redirect("lp_core_tls_dashboard")


@login_required
@permission_required("lp_core_tls_manager.core_tls_manage_duckdns", raise_exception=True)
def tls_duckdns_renew(request):
    cfg = TLSConfig.get_solo()
    token = request.POST.get("duckdns_token", "")
    ok, output = duckdns_renew(token, cfg)
    _log(request, "duckdns-renew", ok, output)
    messages.success(request, "Renouvellement DuckDNS terminé.") if ok else messages.error(request, "Échec renouvellement DuckDNS.")
    return redirect("lp_core_tls_dashboard")
