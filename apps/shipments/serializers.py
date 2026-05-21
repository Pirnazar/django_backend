from rest_framework import serializers
from .models import ShipmentGroup, ShipmentGroupStatusHistory

class ShipmentGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentGroup
        fields = '__all__'
        read_only_fields = ('group_code', 'total_items', 'total_weight_kg', 'total_volume_m3', 'created_at', 'updated_at', 'deleted_at')

class ShipmentGroupStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentGroupStatusHistory
        fields = '__all__'
