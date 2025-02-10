from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Add URL patterns here when we implement the views
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]
