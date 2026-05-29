from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    """Authenticate by email, phone number, or client_code.

    The mobile client logs in by phone number; staff log in by email; a client
    may also be addressed by its client_code. All resolve to a StaffUser.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username:
            return None

        identifier = str(username).strip()
        user = None

        # 1. By email
        user = User.objects.filter(email__iexact=identifier).first()

        # 2. By StaffUser phone number
        if user is None:
            user = User.objects.filter(phone_number=identifier).first()

        # 3. By Client (client_code or phone) → linked user
        if user is None:
            from apps.clients.models import Client
            client = (
                Client.objects.filter(client_code__iexact=identifier).first()
                or Client.objects.filter(phone_number=identifier).first()
            )
            if client and client.user_id:
                user = client.user

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
