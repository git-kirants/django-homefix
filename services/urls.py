from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('request/', views.request_service, name='request_service'),
    path('list/', views.service_list, name='service_list'),
    path('detail/<int:pk>/', views.service_detail, name='service_detail'),
    path('offer/<int:service_id>/', views.make_offer, name='make_offer'),
    path('offer/<int:offer_id>/accept/', views.accept_offer, name='accept_offer'),
    path('offer/<int:offer_id>/reject/', views.reject_offer, name='reject_offer'),
    path('review/<int:service_id>/', views.add_review, name='add_review'),
    
    # Admin actions
    path('approve/<int:service_id>/', views.approve_service, name='approve_service'),
    path('reject/<int:service_id>/', views.reject_service, name='reject_service'),
    
    # Service Provider actions
    path('start/<int:service_id>/', views.start_service, name='start_service'),
    path('complete/<int:service_id>/', views.complete_service, name='complete_service'),
    
    # Client actions
    path('cancel/<int:service_id>/', views.cancel_service, name='cancel_service'),
]
