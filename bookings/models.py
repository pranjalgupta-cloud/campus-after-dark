import uuid
from decimal import Decimal
from django.db import models
from accounts.models import User, OrganizationProfile
from facilities.models import Facility


class PlatformSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def get_commission_rate(cls):
        try:
            setting = cls.objects.get(key='commission_rate')
            return Decimal(setting.value)
        except cls.DoesNotExist:
            return Decimal('10.0')


class Booking(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved_awaiting_payment'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'
    STATUS_PAYMENT_FAILED = 'payment_failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved — Awaiting Payment'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_PAYMENT_FAILED, 'Payment Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    facility = models.ForeignKey(Facility, on_delete=models.PROTECT, related_name='bookings')
    organization = models.ForeignKey(OrganizationProfile, on_delete=models.PROTECT, related_name='bookings')
    booked_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    attendee_count = models.PositiveIntegerField()
    purpose = models.CharField(max_length=500)
    additional_requirements = models.TextField(blank=True)
    # Price snapshot at time of booking
    hours_booked = models.DecimalField(max_digits=6, decimal_places=2)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    institution_payout = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rejection_reason = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='cancelled_bookings'
    )
    reference_number = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.reference_number} — {self.facility.name}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            import random, string
            self.reference_number = 'CAD' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)

    @property
    def duration_display(self):
        h = int(self.hours_booked)
        m = int((self.hours_booked - h) * 60)
        if m:
            return f"{h}h {m}m"
        return f"{h}h"

    @property
    def status_badge_class(self):
        mapping = {
            'pending': 'badge-warning',
            'approved_awaiting_payment': 'badge-info',
            'confirmed': 'badge-success',
            'rejected': 'badge-danger',
            'cancelled': 'badge-secondary',
            'completed': 'badge-primary',
            'payment_failed': 'badge-danger',
        }
        return mapping.get(self.status, 'badge-secondary')


class BookingStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['changed_at']


class Payment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]
    METHOD_DEMO = 'demo'
    METHOD_RAZORPAY = 'razorpay'
    METHOD_CHOICES = [
        (METHOD_DEMO, 'Demo Payment'),
        (METHOD_RAZORPAY, 'Razorpay'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=METHOD_DEMO)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    provider_reference = models.CharField(max_length=200, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} — {self.booking.reference_number} ({self.status})"


class Payout(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSED = 'processed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSED, 'Processed'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name='payout')
    institution = models.ForeignKey('accounts.InstitutionProfile', on_delete=models.PROTECT, related_name='payouts')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.reviewer.email} for {self.facility.name}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('booking_request', 'New Booking Request'),
        ('booking_approved', 'Booking Approved'),
        ('booking_rejected', 'Booking Rejected'),
        ('booking_confirmed', 'Booking Confirmed'),
        ('booking_cancelled', 'Booking Cancelled'),
        ('payment_received', 'Payment Received'),
        ('institution_approved', 'Institution Approved'),
        ('institution_rejected', 'Institution Rejected'),
        ('general', 'General'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='general')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_booking = models.ForeignKey(Booking, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=200)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"
