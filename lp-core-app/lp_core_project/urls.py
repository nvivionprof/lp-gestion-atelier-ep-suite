from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('', views.dashboard, name='core_dashboard'),
    path('login/', views.login_view, name='core_login'),
    path('logout/', views.logout_view, name='core_logout'),
    path('utilisateurs/', views.users_list, name='core_users_list'),
    path('utilisateurs/gestion-eleves/', views.student_lifecycle, name='core_student_lifecycle'),
    path('utilisateurs/<int:pk>/', views.user_detail, name='core_user_detail'),
    path('mon-compte/', views.my_account, name='core_my_account'),
    path('rgpd/', views.rgpd_center, name='core_rgpd'),
    path('magasins/', views.stores_list, name='core_stores_list'),
    path('classes/', views.core_classes, name='core_classes'),
    path('blocs-atelier/', views.atelier_blocks, name='core_atelier_blocks'),
    path('zones-atelier/', views.core_workshop_zones, name='core_workshop_zones'),
    path('droits-par-lot/', views.bulk_permissions, name='core_bulk_permissions'),
    path('parametres-publics/', views.public_settings_view, name='core_public_settings'),
    path('parametres-publics/action/', views.public_settings_server_action, name='core_public_settings_action'),
    path('mises-a-jour/', views.suite_updates_view, name='core_suite_updates'),
    path('sauvegarde-restauration/', views.backup_restore_view, name='core_backup_restore'),
    path('supervision-bases/', views.database_supervision_view, name='core_database_supervision'),
    path('utilisateurs/import/', views.users_import, name='core_users_import'),
    path('utilisateurs/export.csv', views.users_export_csv, name='core_users_export_csv'),
    path('modules/sync-toolmag/', views.sync_toolmag_from_core, name='core_sync_toolmag'),
    path('modules/sync-pedashop/', views.sync_pedashop_from_core, name='core_sync_pedashop'),
    path('modules/sync-safety/', views.sync_safety_from_core, name='core_sync_safety'),
    path('modules/sync-system-manager/', views.sync_system_manager_from_core, name='core_sync_system'),
    path('modules/sync-tpmanager/', views.sync_tpmanager_from_core, name='core_sync_tpmanager'),
    path('modules/sync-pfmp/', views.sync_pfmp_from_core, name='core_sync_pfmp'),
    path('modules/sync-all/', views.sync_all_modules_from_core, name='core_sync_all_modules'),
    path('api/health/', views.api_health, name='core_api_health'),
    path('api/users/', views.api_users, name='core_api_users'),
    path('api/users/<int:user_id>/', views.api_user_detail, name='core_api_user_detail'),
    path('api/classes/', views.api_classes, name='core_api_classes'),
    path('api/formations/', views.api_formations, name='core_api_formations'),
    path('api/atelier-blocks/', views.api_atelier_blocks, name='core_api_atelier_blocks'),
    path('api/workshop-zones/', views.api_workshop_zones, name='core_api_workshop_zones'),
    path('api/system-manager/referentials/import/', views.api_system_manager_referentials_import, name='core_api_system_manager_referentials_import'),
        path('aide/', views.help_view, name='core_help'),
    path('a-propos/', views.about_view, name='core_about'),
    path('admin/', admin.site.urls),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
