from rest_framework import serializers
from .models import Destination, Warehouse

class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = '__all__'

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'
