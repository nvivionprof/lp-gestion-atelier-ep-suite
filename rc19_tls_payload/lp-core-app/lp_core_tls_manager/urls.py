from django.urls import path
from . import views

urlpatterns = [
    path("admin/tls/", views.tls_dashboard, name="lp_core_tls_dashboard"),
    path("admin/tls/save/", views.tls_save_config, name="lp_core_tls_save"),
    path("admin/tls/duckdns/issue/", views.tls_duckdns_issue, name="lp_core_tls_duckdns_issue"),
    path("admin/tls/duckdns/renew/", views.tls_duckdns_renew, name="lp_core_tls_duckdns_renew"),
]
