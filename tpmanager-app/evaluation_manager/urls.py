from django.urls import path
from . import views

app_name = 'evaluation_manager'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('eleve/<int:eleve_pk>/', views.student_dashboard, name='student_dashboard'),
    path('classe/', views.class_dashboard, name='class_dashboard'),
    path('activite/<int:pk>/', views.activity_detail, name='activity_detail'),
    path('bilan/<int:pk>/', views.bilan_detail, name='bilan_detail'),
]
