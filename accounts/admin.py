from django.contrib import admin
from .models import User, InstitutionProfile, OrganizationProfile, InstitutionDocument

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'account_status', 'created_at']
    list_filter = ['role', 'account_status']
    search_fields = ['email', 'first_name', 'last_name']

@admin.register(InstitutionProfile)
class InstitutionProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'verification_status', 'created_at']
    list_filter = ['verification_status']
    search_fields = ['name', 'city']

@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'org_type', 'city', 'created_at']

@admin.register(InstitutionDocument)
class InstitutionDocumentAdmin(admin.ModelAdmin):
    list_display = ['institution', 'doc_type', 'title', 'uploaded_at']
