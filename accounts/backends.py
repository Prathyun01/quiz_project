from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend allowing login with email or username
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return None
        
        try:
            # Since USERNAME_FIELD is 'email', we need to handle both email and username
            if '@' in username:
                # Looks like an email
                user = User.objects.get(email__iexact=username)
            else:
                # Looks like a username
                user = User.objects.get(username__iexact=username)
                
        except User.DoesNotExist:
            # Run default password hasher to prevent timing attacks
            User().set_password(password)
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None

    def user_can_authenticate(self, user):
        """
        Allow active users to authenticate (temporarily ignore email verification)
        """
        is_active = getattr(user, 'is_active', None)
        return is_active
