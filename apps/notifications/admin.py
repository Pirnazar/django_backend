from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.common.admin_helpers import badge

from .models import Notification, NotificationChannel, NotificationStatus, NotificationType


_CHANNEL_COLORS = {
    NotificationChannel.TELEGRAM:  'blue',
    NotificationChannel.SMS:       'green',
    NotificationChannel.WHATSAPP:  'teal',
    NotificationChannel.PUSH:      'violet',
    NotificationChannel.INTERNAL:  'gray',
}

_STATUS_COLORS = {
    NotificationStatus.PENDING:   'amber',
    NotificationStatus.SENT:      'green',
    NotificationStatus.FAILED:    'red',
    NotificationStatus.CANCELLED: 'gray',
}

_TYPE_COLORS = {
    NotificationType.ITEM_RECEIVED:    'blue',
    NotificationType.ITEM_SENT:        'orange',
    NotificationType.ITEM_ARRIVED:     'teal',
    NotificationType.READY_FOR_PICKUP: 'green',
    NotificationType.PAYMENT_DUE:      'red',
    NotificationType.CUSTOM:           'gray',
}


@admin.action(description=_('Отправить выбранные'))
def action_send_selected(modeladmin, request, queryset):
    from .tasks import send_notification_task
    pending = queryset.filter(status=NotificationStatus.PENDING)
    count = pending.count()
    for n in pending:
        send_notification_task.delay(n.pk)
    modeladmin.message_user(request, f'Поставлено в очередь: {count}', messages.SUCCESS)


@admin.action(description=_('Отменить выбранные'))
def action_cancel_selected(modeladmin, request, queryset):
    updated = queryset.filter(status=NotificationStatus.PENDING).update(
        status=NotificationStatus.CANCELLED
    )
    modeladmin.message_user(request, f'Отменено: {updated}', messages.SUCCESS)


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ('_client', '_type', '_channel', '_status', '_item', '_created')
    list_filter  = ('channel', 'type', 'status', 'created_at')
    search_fields = (
        'client__client_code', 'client__full_name', 'client__phone_number',
        'item__item_code',
    )
    readonly_fields = ('sent_at', 'error_message', 'payload', 'created_at', 'updated_at')
    list_select_related = ('client', 'item')
    actions = [action_send_selected, action_cancel_selected]
    ordering = ('-created_at',)

    def _client(self, obj):
        return f'{obj.client.client_code} — {obj.client.full_name}'
    _client.short_description = _('Клиент')
    _client.admin_order_field = 'client__client_code'

    def _type(self, obj):
        color = _TYPE_COLORS.get(obj.type, 'gray')
        return badge(obj.get_type_display(), color)
    _type.short_description = _('Тип')
    _type.admin_order_field = 'type'

    def _channel(self, obj):
        color = _CHANNEL_COLORS.get(obj.channel, 'gray')
        return badge(obj.get_channel_display(), color)
    _channel.short_description = _('Канал')
    _channel.admin_order_field = 'channel'

    def _status(self, obj):
        color = _STATUS_COLORS.get(obj.status, 'gray')
        return badge(obj.get_status_display(), color)
    _status.short_description = _('Статус')
    _status.admin_order_field = 'status'

    def _item(self, obj):
        return obj.item.item_code if obj.item else '—'
    _item.short_description = _('Груз')
    _item.admin_order_field = 'item__item_code'

    def _created(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M') if obj.created_at else '—'
    _created.short_description = _('Создано')
    _created.admin_order_field = 'created_at'

    def has_add_permission(self, request):
        return False
