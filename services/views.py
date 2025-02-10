from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import ServiceCategory, ServiceRequest, ServiceOffer, ServiceReview
from django.db import transaction

# Create your views here.

@login_required
def request_service(request):
    if request.method == 'POST':
        try:
            service = ServiceRequest.objects.create(
                title=request.POST['title'],
                category_id=request.POST['category'],
                description=request.POST['description'],
                client=request.user,
                priority=request.POST['priority'],
                preferred_time=request.POST['preferred_time'],
                location=request.POST['location'],
                estimated_budget=request.POST.get('estimated_budget') or None
            )
            messages.success(request, 'Service request submitted successfully!')
            return redirect('services:service_detail', service.id)
        except Exception as e:
            messages.error(request, f'Error creating service request: {str(e)}')
    
    categories = ServiceCategory.objects.all()
    return render(request, 'services/request_service.html', {'categories': categories})

@login_required
def service_list(request):
    # Base queryset
    queryset = ServiceRequest.objects.select_related('category', 'client', 'service_provider')
    
    # Filter based on user type
    if request.user.user_type in ['homeowner', 'tenant']:
        queryset = queryset.filter(client=request.user)
    elif request.user.user_type == 'service_provider':
        if not request.user.is_approved:
            messages.warning(request, 'Your account is pending approval.')
            return redirect('users:home')
        
        # Get the view type from query params (my_services or all_services)
        view_type = request.GET.get('view', 'all_services')
        
        if view_type == 'my_services':
            # Show services where they've made offers or are assigned
            queryset = queryset.filter(
                Q(offers__service_provider=request.user) |
                Q(service_provider=request.user)
            ).distinct()
        else:
            # Show all available services and their offers
            queryset = queryset.filter(
                Q(status='approved') |
                Q(offers__service_provider=request.user) |
                Q(service_provider=request.user)
            ).distinct()
        
        # Add a flag for requests that match provider's skills
        provider_skills = request.user.serviceproviderprofile.skills.all()
        matching_categories = provider_skills.values_list('id', flat=True)
        
        # Add annotations for provider context
        from django.db.models import Case, When, BooleanField, Exists, OuterRef
        queryset = queryset.annotate(
            matches_skills=Case(
                When(category__in=matching_categories, then=True),
                default=False,
                output_field=BooleanField(),
            ),
            has_made_offer=Exists(
                ServiceOffer.objects.filter(
                    service_request=OuterRef('pk'),
                    service_provider=request.user
                )
            )
        )
    elif request.user.is_staff:
        # Admin can see all requests
        pass
    else:
        # Unauthorized users can't see any requests
        messages.error(request, 'You do not have permission to view service requests.')
        return redirect('users:home')
    
    # Apply filters
    category = request.GET.get('category')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    
    if category:
        queryset = queryset.filter(category_id=category)
    if status:
        queryset = queryset.filter(status=status)
    if priority:
        queryset = queryset.filter(priority=priority)
    
    # Pagination
    paginator = Paginator(queryset.order_by('-created_at'), 10)
    page = request.GET.get('page')
    service_requests = paginator.get_page(page)
    
    context = {
        'service_requests': service_requests,
        'categories': ServiceCategory.objects.all(),
        'status_choices': ServiceRequest.STATUS_CHOICES,
        'priority_choices': ServiceRequest.PRIORITY_CHOICES,
    }
    return render(request, 'services/service_list.html', context)

@login_required
def service_detail(request, pk):
    service = get_object_or_404(ServiceRequest, pk=pk)
    
    # Check if user has permission to view
    if not (request.user.is_staff or 
            request.user == service.client or 
            request.user == service.service_provider or
            (request.user.user_type == 'service_provider' and service.status == 'approved')):
        messages.error(request, 'You do not have permission to view this service request.')
        return redirect('services:service_list')
    
    return render(request, 'services/service_detail.html', {'service': service})

@login_required
def make_offer(request, service_id):
    if request.user.user_type != 'service_provider':
        messages.error(request, 'Only service providers can make offers.')
        return redirect('services:service_list')
    
    service = get_object_or_404(ServiceRequest, pk=service_id)
    
    if request.method == 'POST':
        try:
            ServiceOffer.objects.create(
                service_request=service,
                service_provider=request.user,
                price_quote=request.POST['price_quote'],
                estimated_hours=request.POST['estimated_hours'],
                message=request.POST['message']
            )
            messages.success(request, 'Offer submitted successfully!')
        except Exception as e:
            messages.error(request, f'Error submitting offer: {str(e)}')
    
    return redirect('services:service_detail', service_id)

@login_required
def accept_offer(request, offer_id):
    offer = get_object_or_404(ServiceOffer, pk=offer_id)
    
    if request.user != offer.service_request.client:
        messages.error(request, 'You do not have permission to accept this offer.')
        return redirect('services:service_detail', offer.service_request.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                offer.status = 'accepted'
                offer.save()
                
                service = offer.service_request
                service.service_provider = offer.service_provider
                service.status = 'assigned'
                service.save()
                
                # Reject other offers
                service.offers.exclude(pk=offer.pk).update(status='rejected')
                
            messages.success(request, 'Offer accepted successfully!')
        except Exception as e:
            messages.error(request, f'Error accepting offer: {str(e)}')
    
    return redirect('services:service_detail', offer.service_request.id)

@login_required
def reject_offer(request, offer_id):
    offer = get_object_or_404(ServiceOffer, pk=offer_id)
    
    if request.user != offer.service_request.client:
        messages.error(request, 'You do not have permission to reject this offer.')
        return redirect('services:service_detail', offer.service_request.id)
    
    if request.method == 'POST':
        try:
            offer.status = 'rejected'
            offer.save()
            messages.success(request, 'Offer rejected successfully.')
        except Exception as e:
            messages.error(request, f'Error rejecting offer: {str(e)}')
    
    return redirect('services:service_detail', offer.service_request.id)

@login_required
def add_review(request, service_id):
    service = get_object_or_404(ServiceRequest, pk=service_id)
    
    if request.user != service.client:
        messages.error(request, 'Only the client can review this service.')
        return redirect('services:service_detail', service_id)
    
    if request.method == 'POST':
        try:
            ServiceReview.objects.create(
                service_request=service,
                rating=request.POST['rating'],
                comment=request.POST['comment']
            )
            messages.success(request, 'Review submitted successfully!')
        except Exception as e:
            messages.error(request, f'Error submitting review: {str(e)}')
    
    return redirect('services:service_detail', service_id)

# Admin Actions
@login_required
def approve_service(request, service_id):
    if not request.user.is_staff:
        messages.error(request, 'Only administrators can approve service requests.')
        return redirect('services:service_detail', service_id)
    
    service = get_object_or_404(ServiceRequest, pk=service_id)
    if request.method == 'POST':
        service.status = 'approved'
        service.save()
        messages.success(request, 'Service request approved successfully!')
    
    return redirect('services:service_detail', service_id)

@login_required
def reject_service(request, service_id):
    if not request.user.is_staff:
        messages.error(request, 'Only administrators can reject service requests.')
        return redirect('services:service_detail', service_id)
    
    service = get_object_or_404(ServiceRequest, pk=service_id)
    if request.method == 'POST':
        service.status = 'rejected'
        service.save()
        messages.success(request, 'Service request rejected.')
    
    return redirect('services:service_detail', service_id)

# Service Provider Actions
@login_required
def start_service(request, service_id):
    service = get_object_or_404(ServiceRequest, pk=service_id)
    
    if request.user != service.service_provider:
        messages.error(request, 'Only the assigned service provider can start the service.')
        return redirect('services:service_detail', service_id)
    
    if request.method == 'POST':
        service.status = 'in_progress'
        service.save()
        messages.success(request, 'Service marked as in progress.')
    
    return redirect('services:service_detail', service_id)

@login_required
def complete_service(request, service_id):
    service = get_object_or_404(ServiceRequest, pk=service_id)
    
    if request.user != service.service_provider:
        messages.error(request, 'Only the assigned service provider can complete the service.')
        return redirect('services:service_detail', service_id)
    
    if request.method == 'POST':
        service.status = 'completed'
        service.save()
        messages.success(request, 'Service marked as completed.')
    
    return redirect('services:service_detail', service_id)

# Client Actions
@login_required
def cancel_service(request, service_id):
    service = get_object_or_404(ServiceRequest, pk=service_id)
    
    if request.user != service.client:
        messages.error(request, 'Only the client can cancel the service request.')
        return redirect('services:service_detail', service_id)
    
    if request.method == 'POST':
        service.status = 'cancelled'
        service.save()
        messages.success(request, 'Service request cancelled.')
    
    return redirect('services:service_detail', service_id)
