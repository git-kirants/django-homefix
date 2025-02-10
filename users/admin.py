from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, HomeownerProfile, TenantProfile, 
    ServiceProviderProfile, ServiceProviderCertification, Skill
)

# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_approved', 'is_active')
    list_filter = ('user_type', 'is_approved', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)
    actions = ['approve_users', 'reject_users']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_type', 'is_approved')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def approve_users(self, request, queryset):
        queryset.update(is_approved=True)
    approve_users.short_description = "Approve selected users"

    def reject_users(self, request, queryset):
        queryset.update(is_approved=False)
    reject_users.short_description = "Reject selected users"

@admin.register(HomeownerProfile)
class HomeownerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'property_type', 'created_at')
    search_fields = ('user__username', 'property_type')

@admin.register(TenantProfile)
class TenantProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'lease_start_date', 'lease_end_date')
    search_fields = ('user__username',)

@admin.register(ServiceProviderProfile)
class ServiceProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'average_rating')
    search_fields = ('user__username', 'company_name')
    filter_horizontal = ('certifications', 'skills')

@admin.register(ServiceProviderCertification)
class ServiceProviderCertificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'issuing_authority', 'issue_date', 'expiry_date')
    search_fields = ('name', 'issuing_authority')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
