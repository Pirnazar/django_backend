from rest_framework import viewsets
from .models import Client
from .serializers import ClientSerializer
from apps.common.services import generate_client_code

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    search_fields = ['client_code', 'full_name', 'phone_number']
    filterset_fields = ['is_active', 'default_destination']

