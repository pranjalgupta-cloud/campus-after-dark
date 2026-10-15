from django.contrib import admin
from .models import Facility, FacilityImage, Amenity, BlockedDate

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'institution', 'category', 'city', 'status', 'is_featured']
    list_filter = ['category', 'status', 'is_featured']
    search_fields = ['name', 'city', 'institution__name']

@admin.register(FacilityImage)
class FacilityImageAdmin(admin.ModelAdmin):
    list_display = ['facility', 'is_primary', 'order', 'uploaded_at']

@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display = ['facility', 'blocked_date', 'reason']
