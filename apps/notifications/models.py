from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.models import TimeStampedSoftDeleteModel


class NotificationChannel(models.TextChoices):
    TELEGRAM  = 'telegram',  _('Telegram')
    SMS       = 'sms',       _('SMS')
    WHATSAPP  = 'whatsapp',  _('WhatsApp')
    PUSH      = 'push',      _('Push-уведомление')
    INTERNAL  = 'internal',  _('Внутреннее')


class NotificationType(models.TextChoices):
    ITEM_RECEIVED    = 'item_received',    _('Груз принят')
    ITEM_SENT        = 'item_sent',        _('Груз отправлен')
    ITEM_ARRIVED     = 'item_arrived',     _('Груз прибыл')
    READY_FOR_PICKUP = 'ready_for_pickup', _('Готов к выдаче')
    PAYMENT_DUE      = 'payment_due',      _('Ожидается оплата')
    CUSTOM           = 'custom',           _('Произвольное')


class NotificationStatus(models.TextChoices):
    PENDING   = 'pending',   _('Ожидает')
    SENT      = 'sent',      _('Отправлено')
    FAILED    = 'failed',    _('Ошибка')
    CANCELLED = 'cancelled', _('Отменено')


class Notification(TimeStampedSoftDeleteModel):
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.PROTECT,
        related_name='notifications',
        verbose_name=_('Клиент'),
    )
    item = models.ForeignKey(
        'items.Item',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifications',
        verbose_name=_('Груз'),
    )
    shipment_group = models.ForeignKey(
        'shipments.ShipmentGroup',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notifications',
        verbose_name=_('Партия'),
    )
    channel = models.CharField(
        max_length=20,
        choices=NotificationChannel.choices,
        default=NotificationChannel.INTERNAL,
        verbose_name=_('Канал'),
    )
    type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        verbose_name=_('Тип'),
    )
    title = models.CharField(max_length=255, verbose_name=_('Заголовок'))
    message = models.TextField(verbose_name=_('Сообщение'))
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
        verbose_name=_('Статус'),
    )
    payload = models.JSONField(default=dict, blank=True, verbose_name=_('Данные'))
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Отправлено в'))
    error_message = models.TextField(blank=True, verbose_name=_('Ошибка'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Уведомление')
        verbose_name_plural = _('Уведомления')

    def __str__(self):
        return f'{self.get_type_display()} → {self.client} [{self.get_status_display()}]'
