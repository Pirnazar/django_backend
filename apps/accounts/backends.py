from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        try:
            # 1. Try to find by email
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # 2. Try to find by client_code linked to a user
            from apps.clients.models import Client
            try:
                client = Client.objects.get(client_code__iexact=username)
                if client.user:
                    user = client.user
                else:
                    return None
            except Client.DoesNotExist:
                return None
                
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
