import logging

from django.utils import timezone

from apps.common.choices import DeliveryStatus
from .models import Notification, NotificationChannel, NotificationType, NotificationStatus

logger = logging.getLogger(__name__)

_STATUS_TYPE_MAP = {
    DeliveryStatus.CREATED: (
        NotificationType.ITEM_RECEIVED,
        'Груз принят',
        'Ваш груз {item_code} принят на склад.',
    ),
    DeliveryStatus.AT_CHINA_WAREHOUSE: (
        NotificationType.ITEM_RECEIVED,
        'Груз принят',
        'Ваш груз {item_code} принят на склад.',
    ),
    DeliveryStatus.SENT_TO_TURKMENISTAN: (
        NotificationType.ITEM_SENT,
        'Груз отправлен',
        'Ваш груз {item_code} отправлен в Туркменистан.',
    ),
    DeliveryStatus.ARRIVED_TURKMENISTAN: (
        NotificationType.ITEM_ARRIVED,
        'Груз прибыл',
        'Ваш груз {item_code} прибыл в Туркменистан.',
    ),
    DeliveryStatus.OUT_FOR_DELIVERY: (
        NotificationType.READY_FOR_PICKUP,
        'Груз готов к выдаче',
        'Ваш груз {item_code} готов к выдаче.',
    ),
}


def create_notification_for_item_status(item, status):
    """Creates a Notification for the given status if mapped and not duplicate."""
    if status not in _STATUS_TYPE_MAP:
        return None
    notif_type, title, msg_tpl = _STATUS_TYPE_MAP[status]
    if Notification.objects.filter(item=item, type=notif_type).exists():
        return None
    return Notification.objects.create(
        client=item.client,
        item=item,
        channel=NotificationChannel.INTERNAL,
        type=notif_type,
        title=title,
        message=msg_tpl.format(item_code=item.item_code),
    )


def send_notification(notification):
    from .providers import get_provider
    provider = get_provider(notification.channel)
    try:
        success = provider.send(notification)
        if success:
            mark_sent(notification)
        else:
            mark_failed(notification, 'Провайдер вернул False')
    except Exception as exc:
        mark_failed(notification, str(exc))


def mark_sent(notification):
    notification.status = NotificationStatus.SENT
    notification.sent_at = timezone.now()
    notification.save(update_fields=['status', 'sent_at'])


def mark_failed(notification, error_message=''):
    notification.status = NotificationStatus.FAILED
    notification.error_message = error_message
    notification.save(update_fields=['status', 'error_message'])
