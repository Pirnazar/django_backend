from rest_framework import serializers
from .models import Item, ItemPhoto, Attachment, ItemExpense, ItemStatusHistory
from apps.clients.models import Client

class ItemPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemPhoto
        fields = '__all__'

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = '__all__'

class ItemExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemExpense
        fields = '__all__'

class ItemStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemStatusHistory
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    photos = ItemPhotoSerializer(many=True, read_only=True)
    expenses = ItemExpenseSerializer(many=True, read_only=True)
    client_code = serializers.CharField(write_only=True, required=False)
    client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(), 
        required=False
    )
    
    def validate(self, attrs):
        client = attrs.get('client')
        client_code = attrs.pop('client_code', None)

        if client and client_code:
            raise serializers.ValidationError(
                {"non_field_errors": "Укажите либо client (ID), либо client_code, но не оба."}
            )

        if not client and client_code:
            from apps.clients.models import Client
            try:
                client = Client.objects.get(client_code=client_code)
                attrs['client'] = client
            except Client.DoesNotExist:
                raise serializers.ValidationError(
                    {"client_code": "Клиент с таким кодом не найден"}
                )

        return attrs
    
    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = (
            'item_code', 'calculated_price', 'external_expenses_total',
            'total_price', 'payment_status', 'updated_at', 'deleted_at',
            'main_photo'
        )

    def _abs(self, url):
        if not url:
            return None
        request = self.context.get('request')
        if request and not str(url).startswith('http'):
            return request.build_absolute_uri(url)
        return url

    def to_representation(self, instance):
        """Expose client/destination/warehouse as nested objects (mobile app contract)."""
        rep = super().to_representation(instance)

        if instance.client_id:
            c = instance.client
            rep['client'] = {
                'id': str(c.id),
                'client_code': c.client_code,
                'full_name': c.full_name,
                'phone_number': c.phone_number,
            }
        else:
            rep['client'] = None

        if instance.destination_id:
            d = instance.destination
            rep['destination'] = {
                'id': str(d.id),
                'code': d.code,
                'name': d.name,
                'country_name': d.country_name or '',
            }
        else:
            rep['destination'] = None

        if instance.warehouse_id:
            w = instance.warehouse
            rep['warehouse'] = {
                'id': str(w.id),
                'code': w.code,
                'name': w.name,
                'city': w.city,
                'country': w.country,
            }
        else:
            rep['warehouse'] = None

        for photo in rep.get('photos') or []:
            photo['image_url'] = self._abs(photo.get('file_url') or photo.get('file'))

        return rep
