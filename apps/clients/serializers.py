from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.common.choices import StaffRole
from .models import Client

User = get_user_model()

class ClientSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'deleted_at', 'user')

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        client = super().create(validated_data)

        if password:
            email = f"{client.client_code}@client.cargo.local".lower()
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=client.full_name,
                phone_number=client.phone_number,
                role=StaffRole.CLIENT
            )
            client.user = user
            client.save(update_fields=['user'])

        return client

    @transaction.atomic
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        client = super().update(instance, validated_data)

        if password:
            if client.user:
                client.user.set_password(password)
                client.user.save()
            else:
                email = f"{client.client_code}@client.cargo.local".lower()
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    full_name=client.full_name,
                    phone_number=client.phone_number,
                    role=StaffRole.CLIENT
                )
                client.user = user
                client.save(update_fields=['user'])
                
        return client
