import pytest
from unittest.mock import patch

from apps.common.choices import DeliveryStatus
from apps.common.factories import ItemFactory
from apps.notifications.models import Notification, NotificationStatus, NotificationType
from apps.notifications.services import (
    create_notification_for_item_status,
    send_notification,
)


@pytest.mark.django_db
def test_notification_creates():
    item = ItemFactory()
    n = create_notification_for_item_status(item, DeliveryStatus.AT_CHINA_WAREHOUSE)
    assert n is not None
    assert n.status == NotificationStatus.PENDING
    assert n.client == item.client
    assert n.item == item


@pytest.mark.django_db
def test_item_status_change_creates_notification():
    item = ItemFactory(delivery_status=DeliveryStatus.AT_CHINA_WAREHOUSE)
    item.delivery_status = DeliveryStatus.SENT_TO_TURKMENISTAN
    item.save()
    assert Notification.objects.filter(item=item, type=NotificationType.ITEM_SENT).exists()


@pytest.mark.django_db
def test_duplicate_not_created():
    item = ItemFactory()
    create_notification_for_item_status(item, DeliveryStatus.AT_CHINA_WAREHOUSE)
    n2 = create_notification_for_item_status(item, DeliveryStatus.AT_CHINA_WAREHOUSE)
    assert n2 is None
    assert Notification.objects.filter(item=item).count() == 1


@pytest.mark.django_db
def test_console_provider_marks_sent():
    item = ItemFactory()
    n = create_notification_for_item_status(item, DeliveryStatus.AT_CHINA_WAREHOUSE)
    send_notification(n)
    n.refresh_from_db()
    assert n.status == NotificationStatus.SENT
    assert n.sent_at is not None


@pytest.mark.django_db
def test_failed_provider_marks_failed():
    item = ItemFactory()
    n = create_notification_for_item_status(item, DeliveryStatus.AT_CHINA_WAREHOUSE)
    with patch(
        'apps.notifications.providers.ConsoleNotificationProvider.send',
        side_effect=Exception('network error'),
    ):
        send_notification(n)
    n.refresh_from_db()
    assert n.status == NotificationStatus.FAILED
    assert 'network error' in n.error_message


@pytest.mark.django_db
def test_unmapped_status_creates_no_notification():
    item = ItemFactory()
    n = create_notification_for_item_status(item, DeliveryStatus.MEASURED)
    assert n is None


# ── Client-facing notification API ────────────────────────────────────────────

from rest_framework.test import APIClient
from apps.common.choices import StaffRole
from apps.common.factories import ClientFactory, StaffUserFactory


def _client_user_with_notifications(n=3):
    user = StaffUserFactory(role=StaffRole.CLIENT, is_staff=False)
    client = ClientFactory(user=user)
    for i in range(n):
        Notification.objects.create(
            client=client,
            channel='internal',
            type=NotificationType.ITEM_RECEIVED,
            title=f'Заголовок {i}',
            message=f'Сообщение {i}',
        )
    return user, client


@pytest.mark.django_db
def test_notifications_list_scoped_to_client():
    user, client = _client_user_with_notifications(2)
    # Чужое уведомление
    other = ClientFactory()
    Notification.objects.create(client=other, channel='internal',
                                type=NotificationType.ITEM_SENT, title='X', message='Y')
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.get('/api/v1/notifications/')
    assert resp.status_code == 200
    data = resp.json()
    assert data['count'] == 2
    row = data['results'][0]
    for key in ('id', 'kind', 'title', 'body', 'created_at', 'unread'):
        assert key in row
    assert row['kind'] == 'cargo'
    assert row['unread'] is True


@pytest.mark.django_db
def test_notifications_unread_filter():
    user, client = _client_user_with_notifications(0)
    from django.utils import timezone
    Notification.objects.create(client=client, channel='internal',
                                type=NotificationType.ITEM_RECEIVED, title='a', message='b')
    read = Notification.objects.create(client=client, channel='internal',
                                       type=NotificationType.ITEM_RECEIVED, title='c', message='d',
                                       read_at=timezone.now())
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.get('/api/v1/notifications/?unread=true')
    assert resp.status_code == 200
    ids = [r['id'] for r in resp.json()['results']]
    assert str(read.id) not in ids
    assert len(ids) == 1


@pytest.mark.django_db
def test_notification_mark_read():
    user, client = _client_user_with_notifications(1)
    notif = Notification.objects.filter(client=client).first()
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(f'/api/v1/notifications/{notif.id}/read/')
    assert resp.status_code == 200
    assert resp.json()['unread'] is False
    notif.refresh_from_db()
    assert notif.read_at is not None


@pytest.mark.django_db
def test_notification_mark_all_read():
    user, client = _client_user_with_notifications(3)
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post('/api/v1/notifications/mark-all-read/')
    assert resp.status_code == 200
    assert resp.json()['updated'] == 3
    assert Notification.objects.filter(client=client, read_at__isnull=True).count() == 0


@pytest.mark.django_db
def test_notification_cannot_mark_others():
    user, client = _client_user_with_notifications(0)
    other = ClientFactory()
    foreign = Notification.objects.create(client=other, channel='internal',
                                          type=NotificationType.ITEM_RECEIVED, title='x', message='y')
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post(f'/api/v1/notifications/{foreign.id}/read/')
    assert resp.status_code == 404


# ── Device registration & push routing ────────────────────────────────────────

from apps.notifications.models import DeviceToken, PushService


@pytest.mark.django_db
def test_device_register():
    user, client = _client_user_with_notifications(0)
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post('/api/v1/devices/', {
        'token': 'abc123', 'platform': 'android', 'push_service': 'jpush',
    }, format='json')
    assert resp.status_code == 201
    d = DeviceToken.objects.get(token='abc123')
    assert d.client == client
    assert d.push_service == PushService.JPUSH
    assert d.is_active is True


@pytest.mark.django_db
def test_device_register_is_upsert():
    user, client = _client_user_with_notifications(0)
    api = APIClient()
    api.force_authenticate(user=user)
    api.post('/api/v1/devices/', {'token': 't1', 'platform': 'android', 'push_service': 'fcm'}, format='json')
    api.post('/api/v1/devices/', {'token': 't1', 'platform': 'android', 'push_service': 'jpush'}, format='json')
    assert DeviceToken.objects.filter(token='t1').count() == 1
    assert DeviceToken.objects.get(token='t1').push_service == PushService.JPUSH


@pytest.mark.django_db
def test_device_unregister():
    user, client = _client_user_with_notifications(0)
    DeviceToken.objects.create(client=client, token='t2', push_service='console')
    api = APIClient()
    api.force_authenticate(user=user)
    resp = api.post('/api/v1/devices/unregister/', {'token': 't2'}, format='json')
    assert resp.status_code == 200
    assert DeviceToken.objects.get(token='t2').is_active is False


@pytest.mark.django_db
def test_push_to_devices_routes_without_error():
    from apps.notifications.services import push_to_devices
    user, client = _client_user_with_notifications(0)
    DeviceToken.objects.create(client=client, token='c1', push_service='console')
    DeviceToken.objects.create(client=client, token='j1', push_service='jpush')
    notif = Notification.objects.create(client=client, channel='internal',
                                        type=NotificationType.ITEM_RECEIVED, title='t', message='m')
    # Should not raise even though jpush/fcm are unconfigured stubs
    push_to_devices(notif)


@pytest.mark.django_db
def test_notification_created_in_client_language():
    item = ItemFactory()
    item.client.preferred_language = 'tk'
    item.client.save(update_fields=['preferred_language'])
    n = create_notification_for_item_status(item, DeliveryStatus.AT_CHINA_WAREHOUSE)
    assert n is not None
    assert 'kabul edildi' in n.message  # Turkmen
    assert n.payload.get('item_code') == item.item_code


@pytest.mark.django_db
def test_in_app_relocalizes_by_accept_language():
    user, client = _client_user_with_notifications(0)
    # Stored in Russian
    Notification.objects.create(
        client=client, channel='internal', type=NotificationType.ITEM_SENT,
        title='Груз отправлен', message='Ваш груз ITM1 отправлен в Туркменистан.',
        payload={'item_code': 'ITM1'},
    )
    api = APIClient()
    api.force_authenticate(user=user)
    # Request in Turkmen → re-localized
    resp = api.get('/api/v1/notifications/', HTTP_ACCEPT_LANGUAGE='tk')
    row = resp.json()['results'][0]
    assert row['title'] == 'Ýük ugradyldy'
    assert 'ugradyldy' in row['body']
    # Request in Russian → Russian
    resp_ru = api.get('/api/v1/notifications/', HTTP_ACCEPT_LANGUAGE='ru')
    assert resp_ru.json()['results'][0]['title'] == 'Груз отправлен'


@pytest.mark.django_db
def test_get_push_provider_routing():
    from apps.notifications.providers import (
        get_push_provider, ConsolePushProvider, FCMPushProvider, APNsPushProvider, JPushProvider,
    )
    _, client = _client_user_with_notifications(0)
    assert isinstance(get_push_provider(DeviceToken(client=client, token='a', push_service='console')), ConsolePushProvider)
    assert isinstance(get_push_provider(DeviceToken(client=client, token='b', push_service='fcm')), FCMPushProvider)
    assert isinstance(get_push_provider(DeviceToken(client=client, token='c', push_service='apns')), APNsPushProvider)
    assert isinstance(get_push_provider(DeviceToken(client=client, token='d', push_service='jpush')), JPushProvider)
