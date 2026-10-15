import uuid
from decimal import Decimal
from django.db import models
from accounts.models import InstitutionProfile


class Amenity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Bootstrap icon class e.g. bi-wifi")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'amenities'


class Facility(models.Model):
    CATEGORY_CHOICES = [
        ('classroom', 'Classroom / Seminar Room'),
        ('auditorium', 'Auditorium / Conference Hall'),
        ('computer_lab', 'Computer Laboratory'),
        ('sports_ground', 'Sports Ground'),
        ('indoor_sports', 'Indoor Sports Facility'),
        ('parking', 'Parking Space'),
        ('multipurpose', 'Multipurpose Hall'),
        ('library', 'Library / Reading Room'),
        ('cafeteria', 'Cafeteria / Food Court'),
        ('other', 'Other'),
    ]
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_INACTIVE, 'Inactive'),
    ]
    PRICING_HOURLY = 'hourly'
    PRICING_DAILY = 'daily'
    PRICING_CHOICES = [
        (PRICING_HOURLY, 'Per Hour'),
        (PRICING_DAILY, 'Per Day'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(InstitutionProfile, on_delete=models.CASCADE, related_name='facilities')
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    capacity = models.PositiveIntegerField()
    pricing_model = models.CharField(max_length=10, choices=PRICING_CHOICES, default=PRICING_HOURLY)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    min_booking_hours = models.PositiveIntegerField(default=1)
    max_booking_hours = models.PositiveIntegerField(default=24)
    rules = models.TextField(blank=True)
    permitted_activities = models.TextField(blank=True)
    opening_time = models.TimeField(default='08:00')
    closing_time = models.TimeField(default='20:00')
    available_days = models.CharField(
        max_length=100, default='Mon,Tue,Wed,Thu,Fri,Sat',
        help_text='Comma-separated: Mon,Tue,Wed,Thu,Fri,Sat,Sun'
    )
    amenities = models.ManyToManyField(Amenity, blank=True, through='FacilityAmenity')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} — {self.institution.name}"

    class Meta:
        verbose_name_plural = 'facilities'
        ordering = ['-created_at']

    @property
    def primary_image(self):
        img = self.images.first()
        return img.image.url if img else None

    @property
    def formatted_price(self):
        return f"₹{self.price_per_unit:,.0f}"

    def calculate_price(self, hours):
        return Decimal(str(self.price_per_unit)) * Decimal(str(hours))


class FacilityImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='facility_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'uploaded_at']


class FacilityAmenity(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('facility', 'amenity')
        verbose_name_plural = 'facility amenities'


class AvailabilityRule(models.Model):
    """Recurring availability override rule"""
    DAY_CHOICES = [
        ('Mon', 'Monday'), ('Tue', 'Tuesday'), ('Wed', 'Wednesday'),
        ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday'), ('Sun', 'Sunday'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='availability_rules')
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES)
    is_available = models.BooleanField(default=True)
    open_time = models.TimeField()
    close_time = models.TimeField()

    def __str__(self):
        return f"{self.facility.name} — {self.day_of_week}"


class BlockedDate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='blocked_dates')
    blocked_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('facility', 'blocked_date')

    def __str__(self):
        return f"{self.facility.name} blocked on {self.blocked_date}"
