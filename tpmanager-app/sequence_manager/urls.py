from django.urls import path
from . import views

app_name = 'sequence_manager'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('calendrier/', views.calendar, name='calendar'),
    path('sequences/', views.sequence_list, name='sequence_list'),
    path('sequences/creer/', views.sequence_create, name='sequence_create'),
    path('sequences/<int:pk>/', views.sequence_detail, name='sequence_detail'),
    path('sequences/<int:pk>/dupliquer/', views.sequence_duplicate, name='sequence_duplicate'),
    path('sequences/<int:pk>/formations/ajouter/', views.formation_add, name='formation_add'),
    path('sequences/<int:pk>/vagues/ajouter/', views.wave_add, name='wave_add'),
    path('sequences/<int:pk>/groupes/ajouter/', views.group_add, name='group_add'),
    path('groupes/<int:pk>/membres/', views.group_members, name='group_members'),
    path('sequences/<int:pk>/seances/generer/', views.sessions_generate, name='sessions_generate'),
    path('sequences/<int:pk>/affectations/ajouter/', views.assignment_add, name='assignment_add'),
    path('sequences/<int:pk>/parcours-libre/', views.free_choice, name='free_choice'),
    path('sequences/<int:pk>/competences/', views.skills_by_class, name='skills_by_class'),
]
