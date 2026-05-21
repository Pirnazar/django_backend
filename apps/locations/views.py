from rest_framework import viewsets
from .models import Destination, Warehouse
from .serializers import DestinationSerializer, WarehouseSerializer

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    search_fields = ['code', 'name', 'country_name']
    filterset_fields = ['is_active']

class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    search_fields = ['code', 'name', 'country', 'city']
    filterset_fields = ['is_active']
