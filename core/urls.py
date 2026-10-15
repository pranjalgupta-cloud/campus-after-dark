from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('for-institutions/', views.for_institutions, name='for_institutions'),
    path('for-organizations/', views.for_organizations, name='for_organizations'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    # Dashboards
    path('dashboard/institution/', views.institution_dashboard, name='institution_dashboard'),
    path('dashboard/organization/', views.org_dashboard, name='org_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/institutions/', views.admin_institutions, name='admin_institutions'),
    path('dashboard/admin/institutions/<uuid:pk>/action/', views.admin_approve_institution, name='admin_approve_institution'),
    path('dashboard/admin/users/', views.admin_users, name='admin_users'),
    path('dashboard/admin/users/<uuid:pk>/toggle/', views.admin_toggle_user, name='admin_toggle_user'),
    path('dashboard/admin/bookings/', views.admin_bookings, name='admin_bookings'),
    path('dashboard/admin/settings/', views.admin_settings, name='admin_settings'),
]
