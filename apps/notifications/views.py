"""Client-facing in-app notification API (/api/v1/notifications/)."""
from django.utils import timezone
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification, DeviceToken
from .serializers import ClientNotificationSerializer, DeviceTokenSerializer


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Lists the current client's notifications and marks them read."""
    serializer_class = ClientNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        client = getattr(self.request.user, 'client_profile', None)
        if client is None:
            return Notification.objects.none()
        qs = Notification.objects.filter(client=client)
        unread = self.request.query_params.get('unread')
        if unread in ('true', '1', 'True'):
            qs = qs.filter(read_at__isnull=True)
        return qs

    @action(detail=True, methods=['post'], url_path='read')
    def read(self, request, pk=None):
        notification = self.get_queryset().filter(pk=pk).first()
        if notification is None:
            return Response({'detail': 'Уведомление не найдено.'}, status=status.HTTP_404_NOT_FOUND)
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=['read_at'])
        return Response(ClientNotificationSerializer(notification).data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        client = getattr(request.user, 'client_profile', None)
        if client is None:
            return Response({'updated': 0})
        updated = Notification.objects.filter(
            client=client, read_at__isnull=True
        ).update(read_at=timezone.now())
        return Response({'updated': updated})


class DeviceViewSet(viewsets.GenericViewSet):
    """Register / unregister a push device for the current client."""
    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        client = getattr(request.user, 'client_profile', None)
        if client is None:
            return Response({'detail': 'Профиль клиента не найден.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = DeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        device, _created = DeviceToken.objects.update_or_create(
            token=data['token'],
            defaults={
                'client': client,
                'platform': data.get('platform', 'android'),
                'push_service': data.get('push_service', 'console'),
                'is_active': True,
            },
        )
        return Response(DeviceTokenSerializer(device).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='unregister')
    def unregister(self, request):
        client = getattr(request.user, 'client_profile', None)
        token = request.data.get('token')
        if client and token:
            DeviceToken.objects.filter(client=client, token=token).update(is_active=False)
        return Response({'status': 'ok'})
