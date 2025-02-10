from django.db import models
from django.conf import settings
from services.models import ServiceRequest
from django.db.models import Q

# Create your models here.

class Conversation(models.Model):
    service_request = models.OneToOneField(ServiceRequest, related_name='conversation', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message = models.TextField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-updated_at']),
        ]
    
    def get_participants(self):
        return [self.service_request.client, self.service_request.service_provider]
    
    def __str__(self):
        return f'Conversation for {self.service_request.title}'

class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender', 'receiver', 'is_read']),
        ]
    
    def __str__(self):
        return f'From {self.sender} to {self.receiver}: {self.message[:20]}...'
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update conversation's last message and timestamp
        self.conversation.last_message = self.message
        self.conversation.save()
