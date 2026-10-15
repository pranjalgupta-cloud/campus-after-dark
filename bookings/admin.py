from django.contrib import admin
from .models import Booking, Payment, Review, Notification, PlatformSetting, AuditLog, Payout

@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'updated_at']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'facility', 'organization', 'booked_date', 'status', 'total_amount']
    list_filter = ['status']
    search_fields = ['reference_number', 'facility__name', 'organization__name']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'amount', 'method', 'status', 'paid_at']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['facility', 'reviewer', 'rating', 'is_visible', 'created_at']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'created_at']
    readonly_fields = ['action', 'user', 'model_name', 'object_id', 'details', 'ip_address', 'created_at']

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ['booking', 'institution', 'amount', 'status']
