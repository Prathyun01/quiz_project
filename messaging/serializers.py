from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Message, MessageStatus, MessageReaction

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'profile_picture']

class MessageStatusSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageStatus
        fields = ['recipient', 'is_delivered', 'delivered_at', 'is_read', 'read_at']

class MessageReactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    reaction_display = serializers.CharField(source='get_reaction_type_display', read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ['user', 'reaction_type', 'reaction_display', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    status_set = MessageStatusSerializer(many=True, read_only=True)
    reactions = MessageReactionSerializer(many=True, read_only=True)
    reply_to = serializers.SerializerMethodField()
    attachment_name = serializers.ReadOnlyField()
    attachment_size = serializers.ReadOnlyField()
    is_image = serializers.ReadOnlyField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'message_type', 'content', 'attachment',
            'attachment_name', 'attachment_size', 'is_image', 'reply_to',
            'is_edited', 'edited_at', 'created_at', 'status_set', 'reactions'
        ]
    
    def get_reply_to(self, obj):
        if obj.reply_to:
            return {
                'id': str(obj.reply_to.id),
                'content': obj.reply_to.content[:100],
                'sender': obj.reply_to.sender.display_name,
                'created_at': obj.reply_to.created_at
            }
        return None

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = MessageSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'participants', 'is_group', 'group_name', 'group_description',
            'group_admin', 'created_at', 'updated_at', 'last_message',
            'unread_count', 'other_participant'
        ]
    
    def get_unread_count(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user and user.is_authenticated:
            return MessageStatus.objects.filter(
                message__conversation=obj,
                recipient=user,
                is_read=False
            ).count()
        return 0
    
    def get_other_participant(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user and not obj.is_group:
            other = obj.get_other_participant(user)
            return UserSerializer(other).data if other else None
        return None

class ConversationDetailSerializer(ConversationSerializer):
    messages = serializers.SerializerMethodField()
    
    class Meta(ConversationSerializer.Meta):
        fields = ConversationSerializer.Meta.fields + ['messages']
    
    def get_messages(self, obj):
        messages = obj.message_set.filter(is_deleted=False).order_by('-created_at')[:50]
        return MessageSerializer(messages, many=True, context=self.context).data
