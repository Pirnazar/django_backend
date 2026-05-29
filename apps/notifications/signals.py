import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_save, sender='items.Item')
def _store_old_delivery_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_delivery_status = (
                sender.objects.only('delivery_status').get(pk=instance.pk).delivery_status
            )
        except sender.DoesNotExist:
            instance._old_delivery_status = None
    else:
        instance._old_delivery_status = None


@receiver(post_save, sender='items.Item')
def _create_notification_on_status_change(sender, instance, created, **kwargs):
    old = getattr(instance, '_old_delivery_status', None)
    new = instance.delivery_status
    if created or old == new:
        return
    try:
        from .services import create_notification_for_item_status
        from .tasks import send_notification_task
        notification = create_notification_for_item_status(instance, new)
        if notification:
            send_notification_task.delay(notification.pk)
    except Exception:
        logger.exception('Error creating notification for item %s status %s', instance.pk, new)
