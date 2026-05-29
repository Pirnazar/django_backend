import logging

from django.utils import timezone

from apps.common.choices import DeliveryStatus
from .i18n import localize, normalize_lang, DEFAULT_LANG
from .models import Notification, NotificationChannel, NotificationType, NotificationStatus

logger = logging.getLogger(__name__)

# Delivery status → notification type. Text lives in i18n.NOTIFICATION_TEXT (ru/tk).
_STATUS_TYPE_MAP = {
    DeliveryStatus.CREATED:              NotificationType.ITEM_RECEIVED,
    DeliveryStatus.AT_CHINA_WAREHOUSE:   NotificationType.ITEM_RECEIVED,
    DeliveryStatus.SENT_TO_TURKMENISTAN: NotificationType.ITEM_SENT,
    DeliveryStatus.ARRIVED_TURKMENISTAN: NotificationType.ITEM_ARRIVED,
    DeliveryStatus.OUT_FOR_DELIVERY:     NotificationType.READY_FOR_PICKUP,
}


def create_notification_for_item_status(item, status):
    """Creates a Notification for the given status if mapped and not duplicate.

    Title/message are stored in the client's preferred language; the raw params are
    kept in `payload` so the in-app API can re-localize to the app's current language.
    """
    if status not in _STATUS_TYPE_MAP:
        return None
    notif_type = _STATUS_TYPE_MAP[status]
    if Notification.objects.filter(item=item, type=notif_type).exists():
        return None

    lang = normalize_lang(getattr(item.client, 'preferred_language', None)) or DEFAULT_LANG
    title, message = localize(notif_type, lang, item_code=item.item_code)
    return Notification.objects.create(
        client=item.client,
        item=item,
        channel=NotificationChannel.INTERNAL,
        type=notif_type,
        title=title,
        message=message,
        payload={'item_code': item.item_code},
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


def push_to_devices(notification):
    """Best-effort push to all of the client's active devices.

    Routes each device to its registered push service (FCM / JPush / APNs / …).
    Failures are logged and never affect the in-app notification record.
    """
    from .models import DeviceToken
    from .providers import get_push_provider

    if not notification.client_id:
        return
    devices = DeviceToken.objects.filter(client_id=notification.client_id, is_active=True)
    for device in devices:
        try:
            get_push_provider(device).send_push(notification, device)
        except Exception:
            logger.exception('Push failed for device %s', device.pk)
