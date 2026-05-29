import re

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.common.choices import StaffRole

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Mobile client sends `username` (phone/email/client_code); keep `email` as a
    # fallback for any legacy caller. The auth backend resolves the identifier.
    username_field = 'username'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'] = serializers.CharField(required=False)
        self.fields['email'] = serializers.CharField(required=False)

    def validate(self, attrs):
        identifier = attrs.get('username') or attrs.get('email')
        if not identifier:
            raise serializers.ValidationError(
                {'username': 'Укажите телефон, email или код клиента.'}
            )
        attrs['username'] = identifier
        attrs.pop('email', None)
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        return token

class StaffUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'phone_number', 'role', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'created_at')
        read_only_fields = ('id', 'last_login', 'created_at')

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)


class ClientRegisterSerializer(serializers.Serializer):
    """Self-registration of a client by phone + password (mobile app)."""
    full_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_phone_number(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Укажите номер телефона.')
        from apps.clients.models import Client
        exists = (
            User.objects.filter(phone_number=value).exists()
            or Client.objects.filter(phone_number=value, user__isnull=False).exists()
        )
        if exists:
            raise serializers.ValidationError('Этот номер уже зарегистрирован.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        from apps.clients.models import Client
        phone = validated_data['phone_number']
        digits = re.sub(r'\D', '', phone) or phone
        email = f'client_{digits}@client.local'
        # Гарантируем уникальность синтетического email
        base_email, n = email, 1
        while User.objects.filter(email__iexact=email).exists():
            email = base_email.replace('@', f'_{n}@')
            n += 1

        user = User.objects.create_user(
            email=email,
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            role=StaffRole.CLIENT,
            is_staff=False,
            phone_number=phone,
        )
        Client.objects.create(
            user=user,
            full_name=validated_data['full_name'],
            phone_number=phone,
        )
        return user
