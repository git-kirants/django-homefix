from django.contrib import admin
from .models import ServiceCategory, ServiceRequest, ServiceOffer, ServiceReview

# Register your models here.

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'client', 'service_provider', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('title', 'description', 'client__username', 'service_provider__username')
    date_hierarchy = 'created_at'
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        queryset.update(status='approved')
    approve_requests.short_description = "Approve selected service requests"

    def reject_requests(self, request, queryset):
        queryset.update(status='rejected')
    reject_requests.short_description = "Reject selected service requests"

@admin.register(ServiceOffer)
class ServiceOfferAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'service_provider', 'price_quote', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('service_request__title', 'service_provider__username')
    date_hierarchy = 'created_at'

@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('service_request__title', 'comment')
