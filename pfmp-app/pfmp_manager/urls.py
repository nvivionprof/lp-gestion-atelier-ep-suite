from django.urls import path
from . import views
urlpatterns=[
 path('portal-login/',views.portal_login,name='pfmp_portal_login'),
 path('login/',views.login_view,name='pfmp_login'), path('logout/',views.logout_view,name='pfmp_logout'),
 path('sync-lp-core/',views.sync_lp_core_view,name='pfmp_sync_lp_core'),
 path('',views.dashboard,name='pfmp_dashboard'),
 path('entreprises/',views.company_list,name='pfmp_company_list'),
 path('entreprises/creer/',views.company_create,name='pfmp_company_create'),
 path('entreprises/<int:pk>/',views.company_detail,name='pfmp_company_detail'),
 path('entreprises/<int:company_pk>/contacts/creer/',views.contact_create,name='pfmp_contact_create'),
 path('carte/',views.map_view,name='pfmp_map'),
 path('api/entreprises.geojson/',views.company_geojson,name='pfmp_company_geojson'),
 path('periodes/',views.period_list,name='pfmp_period_list'),
 path('periodes/creer/',views.period_create,name='pfmp_period_create'),
 path('affectations/',views.assignment_list,name='pfmp_assignment_list'),
 path('affectations/creer/',views.assignment_create,name='pfmp_assignment_create'),
 path('affectations/<int:assignment_pk>/demarches/creer/',views.step_create,name='pfmp_step_create'),
 path('annonces/',views.announcement_list,name='pfmp_announcement_list'),
 path('annonces/creer/',views.announcement_create,name='pfmp_announcement_create'),
 path('aide/',views.help_view,name='pfmp_help'), path('a-propos/',views.about_view,name='pfmp_about'),
 path('api/health/',views.api_health,name='pfmp_api_health'),
]
