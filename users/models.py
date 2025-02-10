from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, RegexValidator
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('homeowner', 'Homeowner'),
        ('tenant', 'Tenant'),
        ('service_provider', 'Service Provider'),
        ('admin', 'Admin'),
    )
    
    phone_regex = RegexValidator(
        regex=r'^[789]\d{9}$',
        message="Phone number must start with 7, 8 or 9 and be 10 digits long."
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    is_approved = models.BooleanField(default=False)
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=10,
        error_messages={
            'invalid': "Enter a valid 10-digit phone number starting with 7, 8, or 9."
        }
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class HomeownerProfile(Profile):
    property_type = models.CharField(max_length=50, blank=True)
    property_size = models.CharField(max_length=50, blank=True)

class TenantProfile(Profile):
    lease_start_date = models.DateField(null=True, blank=True)
    lease_end_date = models.DateField(null=True, blank=True)

class ServiceProviderProfile(Profile):
    company_name = models.CharField(max_length=100, blank=True)
    services_offered = models.JSONField(default=list)
    certifications = models.ManyToManyField('ServiceProviderCertification')
    skills = models.ManyToManyField('Skill')
    availability = models.JSONField(default=dict)  # Store weekly availability schedule
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)

class ServiceProviderCertification(models.Model):
    name = models.CharField(max_length=100)
    issuing_authority = models.CharField(max_length=100, blank=True)
    certificate_file = models.FileField(
        upload_to='certifications/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.issuing_authority}"

class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
