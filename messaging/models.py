from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import os

User = get_user_model()

def message_attachment_path(instance, filename):
    """Generate upload path for message attachments"""
    return f'message_attachments/{instance.conversation.id}/{filename}'

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=100, blank=True)
    group_description = models.TextField(blank=True)
    group_admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.is_group:
            return self.group_name or f"Group Chat {self.id}"
        else:
            participants = list(self.participants.all())
            if len(participants) >= 2:
                return f"{participants[0].display_name} & {participants[1].display_name}"
            return f"Conversation {self.id}"
    
    @property
    def last_message(self):
        return self.message_set.order_by('-created_at').first()
    
    def get_other_participant(self, user):
        """Get the other participant in a 1-on-1 conversation"""
        if self.is_group:
            return None
        participants = self.participants.exclude(id=user.id)
        return participants.first() if participants.exists() else None
    
    def mark_as_read(self, user):
        """Mark all messages in conversation as read for a user"""
        MessageStatus.objects.filter(
            message__conversation=self,
            recipient=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('image', 'Image'),
        ('voice', 'Voice'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(blank=True)
    attachment = models.FileField(upload_to=message_attachment_path, blank=True, null=True)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.display_name} in {self.conversation}"
    
    @property
    def attachment_name(self):
        if self.attachment:
            return os.path.basename(self.attachment.name)
        return None
    
    @property
    def attachment_size(self):
        if self.attachment:
            return self.attachment.size
        return 0
    
    @property
    def is_image(self):
        if self.attachment:
            return self.attachment.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))
        return False

class MessageStatus(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='status_set')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    is_delivered = models.BooleanField(default=False)
    delivered_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['message', 'recipient']
    
    def __str__(self):
        return f"Status for {self.message.id} - {self.recipient.display_name}"

class MessageReaction(models.Model):
    REACTION_TYPES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('laugh', '😂'),
        ('wow', '😮'),
        ('sad', '😢'),
        ('angry', '😠'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.display_name} reacted {self.get_reaction_type_display()} to message {self.message.id}"

class ConversationSettings(models.Model):
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE, related_name='settings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_muted = models.BooleanField(default=False)
    muted_until = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    custom_notifications = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['conversation', 'user']
    
    def __str__(self):
        return f"Settings for {self.user.display_name} in {self.conversation}"

class MessageDraft(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['conversation', 'user']
    
    def __str__(self):
        return f"Draft by {self.user.display_name} in {self.conversation}"
