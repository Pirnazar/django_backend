"""Client-facing mobile portal views (/api/v1/client/)."""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.items.models import Item

from .models import AdditionalService, CargoService
from .portal_serializers import (
    ClientProfileSerializer,
    AdditionalServiceSerializer,
    CargoServiceSerializer,
    CargoServiceCreateSerializer,
)


def _client_of(request):
    return getattr(request.user, 'client_profile', None)


class ClientProfileView(APIView):
    """GET / PATCH current client's profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        client = _client_of(request)
        if client is None:
            return Response({'detail': 'Профиль клиента не найден.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ClientProfileSerializer(client, context={'request': request}).data)

    def patch(self, request):
        client = _client_of(request)
        if client is None:
            return Response({'detail': 'Профиль клиента не найден.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClientProfileSerializer(
            client, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AvailableServicesView(APIView):
    """GET list of active additional services the client can request."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        services = AdditionalService.objects.filter(is_active=True)
        return Response(AdditionalServiceSerializer(services, many=True).data)


class CargoServicesView(APIView):
    """GET / POST services requested for a specific cargo (Item)."""
    permission_classes = [IsAuthenticated]

    def _get_item(self, request, cargo_id):
        """Return the item if the requester is allowed to see it, else None."""
        item = Item.objects.filter(pk=cargo_id).select_related('client').first()
        if item is None:
            return None, None
        client = _client_of(request)
        is_client = getattr(request.user, 'role', None) == 'client'
        if is_client:
            if client is None or item.client_id != client.id:
                return None, client
        return item, client

    def get(self, request, cargo_id):
        item, _ = self._get_item(request, cargo_id)
        if item is None:
            return Response({'detail': 'Груз не найден.'}, status=status.HTTP_404_NOT_FOUND)
        qs = item.requested_services.select_related('service').all()
        return Response(CargoServiceSerializer(qs, many=True).data)

    def post(self, request, cargo_id):
        item, client = self._get_item(request, cargo_id)
        if item is None:
            return Response({'detail': 'Груз не найден.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CargoServiceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = AdditionalService.objects.get(pk=serializer.validated_data['service_id'])
        cargo_service = CargoService.objects.create(
            cargo=item,
            client=client or item.client,
            service=service,
            price=service.price,
            currency=service.currency,
            comment=serializer.validated_data.get('comment', ''),
        )
        return Response(
            CargoServiceSerializer(cargo_service).data,
            status=status.HTTP_201_CREATED,
        )
