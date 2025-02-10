from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('messages/', views.message_list, name='message_list'),
    path('conversation/<int:service_id>/', views.conversation, name='conversation'),
    path('send/', views.send_message, name='send_message'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
]
