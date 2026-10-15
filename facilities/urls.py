from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('', views.explore, name='explore'),
    path('<uuid:pk>/', views.facility_detail, name='facility_detail'),
    # Institution management
    path('manage/', views.institution_facilities, name='institution_facilities'),
    path('manage/create/', views.facility_create, name='facility_create'),
    path('manage/<uuid:pk>/edit/', views.facility_edit, name='facility_edit'),
    path('manage/<uuid:pk>/status/', views.facility_toggle_status, name='facility_toggle_status'),
    path('manage/<uuid:pk>/block-date/', views.add_blocked_date, name='add_blocked_date'),
    path('manage/<uuid:pk>/unblock/<uuid:date_pk>/', views.remove_blocked_date, name='remove_blocked_date'),
    path('manage/<uuid:pk>/image/<uuid:image_pk>/delete/', views.delete_facility_image, name='delete_facility_image'),
]
