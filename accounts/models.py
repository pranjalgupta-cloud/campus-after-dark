import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_INSTITUTION = 'institution'
    ROLE_ORGANIZATION = 'organization'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_INSTITUTION, 'Institution'),
        (ROLE_ORGANIZATION, 'Organization'),
        (ROLE_ADMIN, 'Admin'),
    ]
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_PENDING = 'pending'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_SUSPENDED, 'Suspended'),
        (STATUS_PENDING, 'Pending'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ORGANIZATION)
    phone = models.CharField(max_length=15, blank=True)
    account_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    @property
    def is_institution(self):
        return self.role == self.ROLE_INSTITUTION

    @property
    def is_org(self):
        return self.role == self.ROLE_ORGANIZATION

    @property
    def is_platform_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser


class InstitutionProfile(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_SUSPENDED = 'suspended'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Verification'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_SUSPENDED, 'Suspended'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='institution_profile')
    name = models.CharField(max_length=200)
    institution_type = models.CharField(max_length=100, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='institution_logos/', blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rejection_reason = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_verified(self):
        return self.verification_status == self.STATUS_APPROVED


class OrganizationProfile(models.Model):
    ORG_TYPE_CHOICES = [
        ('business', 'Business'),
        ('ngo', 'NGO / Non-profit'),
        ('sports', 'Sports Club'),
        ('event', 'Event Organizer'),
        ('training', 'Training Provider'),
        ('government', 'Government Body'),
        ('other', 'Other'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='org_profile')
    name = models.CharField(max_length=200)
    org_type = models.CharField(max_length=50, choices=ORG_TYPE_CHOICES, default='business')
    registration_number = models.CharField(max_length=100, blank=True)
    gst_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='org_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class InstitutionDocument(models.Model):
    DOC_TYPES = [
        ('registration', 'Registration Certificate'),
        ('tax', 'Tax Document'),
        ('identity', 'Identity Proof'),
        ('other', 'Other'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(InstitutionProfile, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=50, choices=DOC_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='institution_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.institution.name} - {self.title}"
