"""Serializers for the client-facing mobile portal (/api/v1/client/)."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Client, AdditionalService, CargoService

User = get_user_model()


class ClientProfileSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source='phone_number', read_only=True)
    note = serializers.CharField(source='notes', required=False, allow_blank=True)
    photo_url = serializers.SerializerMethodField()
    default_destination = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = (
            'id', 'client_code', 'full_name',
            'phone', 'phone_number',
            'whatsapp', 'wechat', 'preferred_language', 'delivery_city',
            'default_destination', 'profile_photo', 'photo_url', 'note',
        )
        read_only_fields = (
            'id', 'client_code', 'phone',
            'photo_url', 'default_destination',
        )

    def get_photo_url(self, obj):
        if not obj.profile_photo:
            return None
        url = obj.profile_photo.url
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url

    def get_default_destination(self, obj):
        if obj.default_destination_id:
            return obj.default_destination.code
        return None

    def validate_phone_number(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Укажите номер телефона.')
        client_qs = Client.objects.filter(phone_number=value)
        user_qs = User.objects.filter(phone_number=value)
        if self.instance:
            client_qs = client_qs.exclude(pk=self.instance.pk)
            if self.instance.user_id:
                user_qs = user_qs.exclude(pk=self.instance.user_id)
        if client_qs.exists() or user_qs.exists():
            raise serializers.ValidationError('Этот номер уже используется.')
        return value

    def update(self, instance, validated_data):
        new_phone = validated_data.get('phone_number')
        instance = super().update(instance, validated_data)
        # Синхронизируем телефон в связанном StaffUser (логин по телефону)
        if new_phone and instance.user_id and instance.user.phone_number != new_phone:
            instance.user.phone_number = new_phone
            instance.user.save(update_fields=['phone_number'])
        return instance


class AdditionalServiceSerializer(serializers.ModelSerializer):
    price = serializers.FloatField()

    class Meta:
        model = AdditionalService
        fields = ('id', 'name', 'description', 'price', 'currency', 'requires_comment')


class CargoServiceSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    cargo_id = serializers.CharField(read_only=True)
    service_id = serializers.IntegerField(read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    price = serializers.FloatField(read_only=True)

    class Meta:
        model = CargoService
        fields = (
            'id', 'cargo_id', 'service_id', 'service_name',
            'status', 'price', 'currency', 'comment', 'created_at',
        )


class CargoServiceCreateSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()
    comment = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_service_id(self, value):
        if not AdditionalService.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError('Услуга не найдена или недоступна.')
        return value
