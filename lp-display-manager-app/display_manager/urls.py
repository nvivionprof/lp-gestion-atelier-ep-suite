from django.urls import path

from . import views

app_name = 'display_manager'

urlpatterns = [
    path('login/', views.local_login, name='login'),
    path('logout/', views.local_logout, name='logout'),
    path('portal-login/', views.portal_login, name='portal_login'),
    path('', views.dashboard, name='dashboard'),
    path('screens/', views.screens, name='screens'),
    path('screens/new/', views.screen_create, name='screen_create'),
    path('screens/<int:pk>/', views.screen_detail, name='screen_detail'),
    path('screens/<int:pk>/edit/', views.screen_edit, name='screen_edit'),
    path('screens/<int:pk>/command/<str:action>/', views.send_command, name='send_command'),

    path('layouts/', views.layouts, name='layouts'),
    path('layouts/new/', views.layout_create, name='layout_create'),
    path('layouts/<int:pk>/edit/', views.layout_edit, name='layout_edit'),
    path('layouts/<int:pk>/duplicate/', views.layout_duplicate, name='layout_duplicate'),
    path('zone-items/<int:pk>/delete/', views.zone_item_delete, name='zone_item_delete'),

    path('medias/', views.media_library, name='media_library'),
    path('medias/<int:pk>/delete/', views.media_delete, name='media_delete'),
    path('qr/', views.qr_actions, name='qr_actions'),

    path('player/<str:token>/', views.player, name='player'),
    path('api/player/<str:token>/manifest/', views.api_manifest, name='api_manifest'),
    path('api/player/<str:token>/heartbeat/', views.api_heartbeat, name='api_heartbeat'),
    path('api/player/<str:token>/commands/', views.api_commands, name='api_commands'),
    path('api/player/<str:token>/commands/<int:command_id>/result/', views.api_command_result, name='api_command_result'),

    path('q/<str:token>/', views.qr_execute, name='qr_execute'),
]
