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
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Прочитано в'))
    error_message = models.TextField(blank=True, verbose_name=_('Ошибка'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Уведомление')
        verbose_name_plural = _('Уведомления')

    def __str__(self):
        return f'{self.get_type_display()} → {self.client} [{self.get_status_display()}]'


class DevicePlatform(models.TextChoices):
    ANDROID = 'android', _('Android')
    IOS = 'ios', _('iOS')


class PushService(models.TextChoices):
    """Which push transport the device registered with.

    The mobile app decides at runtime which service it can use (e.g. checks for
    Google Play services; uses a China OEM channel / aggregator otherwise) and
    registers its token under that service. The backend routes by this value.
    """
    CONSOLE = 'console', _('Console (dev)')
    FCM     = 'fcm',     _('Firebase (Android Global)')
    JPUSH   = 'jpush',   _('JPush 极光 (China)')
    GETUI   = 'getui',   _('GeTui 个推 (China)')
    UMENG   = 'umeng',   _('Umeng 友盟 (China)')
    HUAWEI  = 'huawei',  _('Huawei Push')
    APNS    = 'apns',    _('Apple APNs (iOS)')


class DeviceToken(TimeStampedSoftDeleteModel):
    client = models.ForeignKey(
        'clients.Client', on_delete=models.CASCADE, related_name='devices',
        verbose_name=_('Клиент'),
    )
    token = models.CharField(_('Токен'), max_length=512, unique=True, db_index=True)
    platform = models.CharField(
        max_length=10, choices=DevicePlatform.choices, default=DevicePlatform.ANDROID,
        verbose_name=_('Платформа'),
    )
    push_service = models.CharField(
        max_length=20, choices=PushService.choices, default=PushService.CONSOLE,
        verbose_name=_('Push-сервис'),
    )
    is_active = models.BooleanField(_('Активно'), default=True)
    last_seen_at = models.DateTimeField(_('Последняя активность'), auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Устройство')
        verbose_name_plural = _('Устройства (push)')

    def __str__(self):
        return f'{self.client} · {self.push_service}/{self.platform}'
