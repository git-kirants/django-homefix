from django.db import models
from django.conf import settings
from django.utils import timezone

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class name")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Service Categories"

class ServiceRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
    )
    
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    )
    
    title = models.CharField(max_length=200)
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT)
    description = models.TextField()
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_requests'
    )
    service_provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_services'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    preferred_time = models.DateTimeField()
    location = models.TextField()
    estimated_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.client.username}"

class ServiceOffer(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    service_provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_offers'
    )
    price_quote = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_hours = models.PositiveIntegerField()
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Offer for {self.service_request.title} by {self.service_provider.username}"

class ServiceReview(models.Model):
    service_request = models.OneToOneField(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='review'
    )
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review for {self.service_request.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update service provider's average rating
        if self.service_request.service_provider:
            provider_profile = self.service_request.service_provider.serviceproviderprofile
            reviews = ServiceReview.objects.filter(
                service_request__service_provider=self.service_request.service_provider
            )
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            provider_profile.average_rating = avg_rating
            provider_profile.save()
