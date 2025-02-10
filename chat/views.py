from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count, F
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from .models import ChatMessage, Conversation
from services.models import ServiceRequest
from users.models import User
import json

MESSAGES_PER_PAGE = 50

@login_required
def message_list(request):
    # Get all conversations for the current user
    conversations = (
        Conversation.objects.filter(
            Q(service_request__client=request.user) | Q(service_request__service_provider=request.user)
        ).select_related('service_request')
        .annotate(
            unread_count=Count(
                'messages',
                filter=Q(messages__receiver=request.user, messages__is_read=False)
            )
        )
        .order_by('-updated_at')
    )
    
    return render(request, 'chat/message_list.html', {
        'conversations': conversations
    })

@login_required
def conversation(request, service_id):
    service = get_object_or_404(ServiceRequest, pk=service_id)
    
    # Get or create conversation
    conversation, created = Conversation.objects.get_or_create(service_request=service)
    
    # Mark all messages in this conversation as read
    ChatMessage.objects.filter(
        conversation=conversation,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)
    
    # Get messages with pagination
    page = request.GET.get('page', 1)
    messages = ChatMessage.objects.filter(conversation=conversation).select_related('sender', 'receiver')
    paginator = Paginator(messages, MESSAGES_PER_PAGE)
    messages_page = paginator.get_page(page)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        messages_data = [{
            'id': msg.id,
            'sender': msg.sender_id,
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat(),
            'is_read': msg.is_read
        } for msg in messages_page]
        return JsonResponse({
            'messages': messages_data,
            'has_next': messages_page.has_next(),
            'has_previous': messages_page.has_previous(),
            'total_pages': paginator.num_pages
        })
    
    return render(request, 'chat/conversation.html', {
        'messages': messages_page,
        'service': service,
        'conversation': conversation
    })

@login_required
def send_message(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        service_id = data.get('service_id')
        message_text = data.get('message')
        
        service = get_object_or_404(ServiceRequest, pk=service_id)
        conversation = get_object_or_404(Conversation, service_request=service)
        
        # Determine the receiver (if sender is client, receiver is provider and vice versa)
        receiver = service.service_provider if request.user == service.client else service.client
        
        if not receiver:
            return JsonResponse({'error': 'No receiver found for this message'}, status=400)
        
        message = ChatMessage.objects.create(
            conversation=conversation,
            sender=request.user,
            receiver=receiver,
            message=message_text
        )
        
        return JsonResponse({
            'message': {
                'id': message.id,
                'sender': message.sender_id,
                'message': message.message,
                'timestamp': message.timestamp.isoformat(),
                'is_read': message.is_read
            }
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_unread_count(request):
    unread_count = ChatMessage.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({'unread_count': unread_count})
