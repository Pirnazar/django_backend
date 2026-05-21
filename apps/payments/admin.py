from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from .models import PaymentTransaction
from apps.common.choices import PaymentTransactionStatus, PaymentTransactionType, PaymentMethod
from apps.common.admin_helpers import badge, money, RussianLabelsMixin, PAYMENT_LABELS


_TX_STATUS = {
    PaymentTransactionStatus.PENDING:   ('amber', 'В ожидании'),
    PaymentTransactionStatus.COMPLETED: ('green', 'Завершён'),
    PaymentTransactionStatus.FAILED:    ('red',   'Ошибка'),
    PaymentTransactionStatus.CANCELLED: ('gray',  'Отменён'),
}

_TX_TYPE = {
    PaymentTransactionType.PAYMENT: ('blue',   'Платёж'),
    PaymentTransactionType.REFUND:  ('purple', 'Возврат'),
}

_TX_METHOD = {
    PaymentMethod.CASH:          ('green',  'Наличные'),
    PaymentMethod.CARD:          ('blue',   'Карта'),
    PaymentMethod.BANK_TRANSFER: ('indigo', 'Банк. перевод'),
    PaymentMethod.WECHAT:        ('teal',   'WeChat'),
    PaymentMethod.ALIPAY:        ('sky',    'Alipay'),
}


@admin.action(description=_("Отметить как 'Завершён'"))
def mark_completed(modeladmin, request, queryset):
    queryset.update(status=PaymentTransactionStatus.COMPLETED)


@admin.action(description=_("Отменить платежи"))
def mark_cancelled(modeladmin, request, queryset):
    queryset.update(status=PaymentTransactionStatus.CANCELLED)


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(RussianLabelsMixin, ModelAdmin):
    form_labels = PAYMENT_LABELS
    show_full_result_count = False
    list_select_related = ('item', 'client', 'created_by')

    list_display = (
        'id', '_client', '_item',
        '_amount', '_method', '_status', '_type',
        '_paid_at', '_created_by', '_created',
    )
    list_display_links = ('id',)
    list_filter = ('method', 'status', 'transaction_type', 'currency', 'paid_at', 'created_at')
    search_fields = (
        'item__item_code', 'client__client_code',
        'client__full_name', 'client__phone_number',
        'reference_number',
    )
    autocomplete_fields = ('item', 'client', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    actions = [mark_completed, mark_cancelled]

    fieldsets = (
        (_('Платёж'), {
            'fields': (
                'client', 'item',
                'amount', 'currency', 'method',
                'transaction_type', 'status',
                'paid_at', 'reference_number',
            ),
        }),
        (_('Комментарий'), {
            'fields': ('comment',),
            'classes': ('collapse',),
        }),
        (_('Системная информация'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def _client(self, obj):
        if obj.client:
            return f'{obj.client.client_code} — {obj.client.full_name[:16]}'
        return '—'
    _client.short_description = _('Клиент')
    _client.admin_order_field = 'client__client_code'

    def _item(self, obj):
        return obj.item.item_code if obj.item else '—'
    _item.short_description = _('Груз')
    _item.admin_order_field = 'item__item_code'

    def _amount(self, obj):
        return money(obj.amount, obj.currency)
    _amount.short_description = _('Сумма')
    _amount.admin_order_field = 'amount'

    def _status(self, obj):
        color, label = _TX_STATUS.get(obj.status, ('gray', obj.status))
        return badge(label, color)
    _status.short_description = _('Статус')
    _status.admin_order_field = 'status'

    def _type(self, obj):
        color, label = _TX_TYPE.get(obj.transaction_type, ('gray', obj.transaction_type))
        return badge(label, color)
    _type.short_description = _('Тип')
    _type.admin_order_field = 'transaction_type'

    def _method(self, obj):
        color, label = _TX_METHOD.get(obj.method, ('gray', obj.method))
        return badge(label, color)
    _method.short_description = _('Метод')
    _method.admin_order_field = 'method'

    def _paid_at(self, obj):
        if obj.paid_at:
            return obj.paid_at.strftime('%d.%m.%Y %H:%M')
        return '—'
    _paid_at.short_description = _('Дата оплаты')
    _paid_at.admin_order_field = 'paid_at'

    def _created_by(self, obj):
        return obj.created_by.full_name if obj.created_by else '—'
    _created_by.short_description = _('Создал')
    _created_by.admin_order_field = 'created_by__full_name'

    def _created(self, obj):
        return obj.created_at.strftime('%d.%m.%Y')
    _created.short_description = _('Дата создания')
    _created.admin_order_field = 'created_at'
