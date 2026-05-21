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
