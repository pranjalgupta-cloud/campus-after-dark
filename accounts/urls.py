from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_choice, name='register'),
    path('register/institution/', views.register_institution, name='register_institution'),
    path('register/organization/', views.register_organization, name='register_organization'),
    path('setup/', views.institution_setup, name='institution_setup'),
    path('profile/', views.profile_view, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
