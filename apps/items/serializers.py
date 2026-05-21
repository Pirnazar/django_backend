from rest_framework import serializers
from .models import Item, ItemPhoto, Attachment, ItemExpense, ItemStatusHistory, Box
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
            'total_price', 'payment_status', 'created_at', 'updated_at', 'deleted_at',
            'main_photo'
        )


class BoxItemBriefSerializer(serializers.ModelSerializer):
    client_code = serializers.CharField(source='client.client_code', read_only=True)
    client_name = serializers.CharField(source='client.full_name', read_only=True)

    class Meta:
        model = Item
        fields = (
            'id', 'item_code', 'barcode',
            'client_code', 'client_name',
            'weight_kg', 'volume_m3',
        )


class BoxSerializer(serializers.ModelSerializer):
    items = BoxItemBriefSerializer(many=True, read_only=True)
    destination_code = serializers.CharField(source='destination.code', read_only=True)
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)
    print_payload = serializers.SerializerMethodField()

    class Meta:
        model = Box
        fields = (
            'id', 'box_code', 'barcode', 'status',
            'destination', 'destination_code',
            'warehouse', 'warehouse_code',
            'shipment_group',
            'total_items', 'total_weight_kg', 'total_volume_m3',
            'comment',
            'created_at', 'closed_at', 'printed_at',
            'created_by', 'closed_by',
            'items', 'print_payload',
        )
        read_only_fields = (
            'box_code', 'status',
            'total_items', 'total_weight_kg', 'total_volume_m3',
            'created_at', 'closed_at', 'printed_at',
            'created_by', 'closed_by',
        )

    def get_print_payload(self, obj):
        from .services import box_print_payload
        return box_print_payload(obj)
