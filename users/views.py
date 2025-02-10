from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .models import User, HomeownerProfile, TenantProfile, ServiceProviderProfile, Skill, ServiceProviderCertification
from django.db import transaction

# Create your views here.

def home(request):
    return render(request, 'users/home.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_approved or user.is_superuser:
                login(request, user)
                messages.success(request, 'Successfully logged in!')
                return redirect('users:home')
            else:
                messages.warning(request, 'Your account is pending approval.')
    return render(request, 'users/login.html')

def register(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=request.POST['username'],
                    email=request.POST['email'],
                    password=request.POST['password1'],
                    user_type=request.POST['user_type'],
                    phone_number=request.POST['phone_number']
                )
                
                # Create corresponding profile based on user type
                if user.user_type == 'homeowner':
                    HomeownerProfile.objects.create(user=user)
                elif user.user_type == 'tenant':
                    TenantProfile.objects.create(user=user)
                elif user.user_type == 'service_provider':
                    ServiceProviderProfile.objects.create(user=user)
                
                messages.success(request, 'Registration successful! Please wait for admin approval.')
                return redirect('users:login')
        except Exception as e:
            messages.error(request, str(e))
    return render(request, 'users/register.html')

@login_required
def profile(request):
    user = request.user
    profile = None
    all_skills = []

    # Get the appropriate profile based on user type
    if user.user_type == 'homeowner':
        profile = user.homeownerprofile
    elif user.user_type == 'tenant':
        profile = user.tenantprofile
    elif user.user_type == 'service_provider':
        profile = user.serviceproviderprofile
        all_skills = Skill.objects.all()

    if request.method == 'POST':
        try:
            # Update user information
            user.email = request.POST.get('email')
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.phone_number = request.POST.get('phone_number')
            user.save()

            # Update profile picture if provided
            if request.FILES.get('profile_picture'):
                profile.profile_picture = request.FILES['profile_picture']

            # Update profile-specific fields
            if user.user_type == 'homeowner':
                profile.property_type = request.POST.get('property_type')
                profile.property_size = request.POST.get('property_size')
            elif user.user_type == 'tenant':
                profile.lease_start_date = request.POST.get('lease_start_date')
                profile.lease_end_date = request.POST.get('lease_end_date')
            elif user.user_type == 'service_provider':
                profile.company_name = request.POST.get('company_name')
                # Update skills
                selected_skills = request.POST.getlist('skills')
                profile.skills.set(selected_skills)
                
                # Handle new certification
                if (request.POST.get('cert_name') and request.FILES.get('cert_file')):
                    cert = ServiceProviderCertification.objects.create(
                        name=request.POST.get('cert_name'),
                        issuing_authority=request.POST.get('cert_authority', ''),
                        certificate_file=request.FILES['cert_file'],
                        issue_date=request.POST.get('cert_issue_date') or None,
                        expiry_date=request.POST.get('cert_expiry_date') or None
                    )
                    profile.certifications.add(cert)

            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')

    context = {
        'profile': profile,
        'all_skills': all_skills
    }
    return render(request, 'users/profile.html', context)

@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Successfully logged out!')
    return redirect('users:home')
