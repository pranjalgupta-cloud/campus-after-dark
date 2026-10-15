from django.urls import path
from . import views

urlpatterns = [
    path('request/<uuid:facility_pk>/', views.request_booking, name='request_booking'),
    path('<uuid:pk>/', views.booking_detail, name='booking_detail'),
    path('<uuid:pk>/approve/', views.approve_booking, name='approve_booking'),
    path('<uuid:pk>/reject/', views.reject_booking, name='reject_booking'),
    path('<uuid:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('<uuid:pk>/complete/', views.mark_booking_completed, name='mark_booking_completed'),
    path('<uuid:pk>/payment/', views.payment_page, name='payment_page'),
    path('<uuid:pk>/payment/process/', views.process_payment, name='process_payment'),
    path('<uuid:pk>/review/', views.submit_review, name='submit_review'),
    path('my/', views.org_bookings, name='org_bookings'),
    path('manage/', views.institution_bookings, name='institution_bookings'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
]
