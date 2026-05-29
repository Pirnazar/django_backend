import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_task(self, notification_id):
    from .models import Notification
    from .services import send_notification, push_to_devices
    try:
        notification = Notification.objects.get(pk=notification_id)
    except Notification.DoesNotExist:
        logger.warning('Notification %s not found, skipping', notification_id)
        return
    send_notification(notification)       # in-app/console запись
    push_to_devices(notification)         # best-effort push на устройства (FCM/JPush/APNs)
