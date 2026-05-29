from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from .models import Item, ItemPhoto, Attachment, ItemExpense, ItemStatusHistory
from apps.common.choices import DeliveryStatus, PaymentStatus, WarehouseStage
from apps.common.admin_helpers import badge, money, photo_preview, RussianLabelsMixin, ITEM_LABELS
from apps.items.bulk_actions import (
    action_add_to_group, action_change_status,
    action_export_excel, action_label_preview,
)


# ── Status colour maps ─────────────────────────────────────────────────────────

_DELIVERY = {
    DeliveryStatus.CREATED:              ('gray',   'Создан'),
    DeliveryStatus.AT_CHINA_WAREHOUSE:   ('blue',   'На складе (КНР)'),
    DeliveryStatus.MEASURED:             ('sky',    'Измерен'),
    DeliveryStatus.PHOTOGRAPHED:         ('violet', 'Сфотографирован'),
    DeliveryStatus.LABELED:              ('cyan',   'Маркирован'),
    DeliveryStatus.PACKED:               ('amber',  'Упакован'),
    DeliveryStatus.GROUPED:              ('indigo', 'В партии'),
    DeliveryStatus.SENT_TO_URUMQI:       ('orange', 'Отправлен→Урумчи'),
    DeliveryStatus.ARRIVED_URUMQI:       ('teal',   'Прибыл Урумчи'),
    DeliveryStatus.SENT_TO_TURKMENISTAN: ('orange', 'Отправлен→ТМ'),
    DeliveryStatus.ARRIVED_TURKMENISTAN: ('teal',   'Прибыл в ТМ'),
    DeliveryStatus.OUT_FOR_DELIVERY:     ('green',  'На доставке'),
    DeliveryStatus.DELIVERED:            ('green',  'Доставлен'),
    DeliveryStatus.CANCELLED:            ('red',    'Отменён'),
}

_PAYMENT = {
    PaymentStatus.UNPAID:         ('red',    'Не оплачено'),
    PaymentStatus.PARTIALLY_PAID: ('amber',  'Частично'),
    PaymentStatus.PAID:           ('green',  'Оплачено'),
    PaymentStatus.REFUNDED:       ('purple', 'Возврат'),
}

_STAGE = {
    WarehouseStage.INTAKE:       ('gray',   'Приёмка'),
    WarehouseStage.MEASURED:     ('blue',   'Измерение'),
    WarehouseStage.PHOTOGRAPHED: ('violet', 'Фото'),
    WarehouseStage.LABELED:      ('cyan',   'Маркировка'),
    WarehouseStage.PACKED:       ('amber',  'Упаковка'),
    WarehouseStage.GROUPED:      ('indigo', 'В партии'),
    WarehouseStage.DISPATCHED:   ('green',  'Отправлен'),
}


# ── Inlines ────────────────────────────────────────────────────────────────────

class ItemPhotoInline(TabularInline):
    model = ItemPhoto
    extra = 0
    fields = ('_preview', 'file', 'file_name', 'file_size', 'uploaded_by', 'created_at')
    readonly_fields = ('_preview', 'file_size', 'uploaded_by', 'created_at')
    verbose_name = _('Фото')
    verbose_name_plural = _('Фото груза')

    def _preview(self, obj):
        return photo_preview(obj.file, max_px=70)
    _preview.short_description = _('Превью')


class AttachmentInline(TabularInline):
    model = Attachment
    extra = 0
    fields = ('file_type', 'file', 'file_name', 'file_size', 'uploaded_by', 'created_at')
    readonly_fields = ('file_size', 'uploaded_by', 'created_at')
    verbose_name = _('Вложение')
    verbose_name_plural = _('Вложения')


class ItemExpenseInline(TabularInline):
    model = ItemExpense
    extra = 0
    fields = ('expense_type', 'amount', 'currency', 'comment', 'created_by', 'created_at')
    readonly_fields = ('created_by', 'created_at')
    verbose_name = _('Доп. расход')
    verbose_name_plural = _('Доп. расходы')


class ItemStatusHistoryInline(TabularInline):
    model = ItemStatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'comment', 'changed_by', 'created_at')
    can_delete = False
    max_num = 0
    verbose_name = _('Запись')
    verbose_name_plural = _('История статусов')

    def has_add_permission(self, request, obj=None):
        return False


# ── Bulk actions ───────────────────────────────────────────────────────────────

@admin.action(description=_("Отметить как 'Измерен'"))
def mark_as_measured(modeladmin, request, queryset):
    queryset.update(delivery_status=DeliveryStatus.MEASURED, warehouse_stage=WarehouseStage.MEASURED)


@admin.action(description=_("Отметить как 'Сфотографирован'"))
def mark_as_photographed(modeladmin, request, queryset):
    queryset.update(delivery_status=DeliveryStatus.PHOTOGRAPHED, warehouse_stage=WarehouseStage.PHOTOGRAPHED)


@admin.action(description=_("Отметить как 'Упакован'"))
def mark_as_packed(modeladmin, request, queryset):
    queryset.update(delivery_status=DeliveryStatus.PACKED, warehouse_stage=WarehouseStage.PACKED)


@admin.action(description=_("Отметить как 'Доставлен'"))
def mark_as_delivered(modeladmin, request, queryset):
    queryset.update(delivery_status=DeliveryStatus.DELIVERED)


@admin.action(description=_("Пересчитать выбранные цены"))
def recalculate_prices(modeladmin, request, queryset):
    from apps.items.services import calculate_item_totals
    for item in queryset:
        calculate_item_totals(item)
        item.save(update_fields=['volume_m3', 'calculated_price', 'external_expenses_total', 'total_price'])


# ── Main admin ─────────────────────────────────────────────────────────────────

@admin.register(Item)
class ItemAdmin(RussianLabelsMixin, ModelAdmin):
    form_labels = ITEM_LABELS
    warn_unsaved_changes = True
    show_full_result_count = False
    list_select_related = ('client', 'destination', 'warehouse', 'shipment_group')

    list_display = (
        '_code', '_client', '_destination', '_warehouse', '_group',
        '_weight', '_volume', '_total',
        '_payment', '_delivery', '_stage', '_created',
    )
    list_display_links = ('_code',)
    list_filter = (
        'destination', 'warehouse', 'payment_status', 'delivery_status',
        'warehouse_stage', 'item_type', 'transport_type',
        'is_fragile', 'has_battery', 'is_dangerous', 'requires_manual_review',
        'created_at',
    )
    search_fields = (
        'item_code', 'barcode', 'qr_code', 'express_code',
        'client__client_code', 'client__full_name', 'client__phone_number',
        'shipment_group__group_code',
    )
    readonly_fields = (
        'item_code', '_main_photo',
        'calculated_price', 'external_expenses_total', 'total_price',
        'created_at', 'updated_at',
    )
    autocomplete_fields = ('client', 'destination', 'warehouse', 'shipment_group', 'price_rule')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'item_code', '_main_photo',
                'barcode', 'qr_code', 'express_code',
                'item_type', 'transport_type', 'place_count',
            ),
        }),
        (_('Клиент и направление'), {
            'fields': ('client', 'destination', 'warehouse', 'shipment_group'),
        }),
        (_('Вес и объём'), {
            'fields': (
                'weight_kg', 'length_cm', 'width_cm', 'height_cm',
                'volume_source', 'volume_m3',
            ),
        }),
        (_('Стоимость и оплата'), {
            'fields': (
                'price_rule',
                'declared_value', 'declared_value_currency',
                'calculated_price', 'external_expenses_total', 'total_price',
                'payment_type', 'payment_status',
            ),
        }),
        (_('Статусы'), {
            'fields': ('delivery_status', 'warehouse_stage'),
        }),
        (_('Особенности груза'), {
            'fields': ('is_fragile', 'has_battery', 'is_dangerous', 'requires_manual_review', 'is_repacked'),
            'classes': ('collapse',),
        }),
        (_('Комментарии'), {
            'fields': ('description', 'comment'),
            'classes': ('collapse',),
        }),
        (_('Системная информация'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    inlines = [ItemPhotoInline, AttachmentInline, ItemExpenseInline, ItemStatusHistoryInline]
    actions = [
        mark_as_measured, mark_as_photographed, mark_as_packed, mark_as_delivered,
        recalculate_prices,
        action_add_to_group, action_change_status,
        action_export_excel, action_label_preview,
    ]

    # ── Column methods ─────────────────────────────────────────────────────────

    def _main_photo(self, obj):
        return photo_preview(obj.main_photo, max_px=300)
    _main_photo.short_description = _('Основное фото')

    def _code(self, obj):
        return format_html('<span class="cg-code">{}</span>', obj.item_code)
    _code.short_description = _('Код груза')
    _code.admin_order_field = 'item_code'

    def _client(self, obj):
        if not obj.client:
            return '—'
        url = reverse('admin:clients_client_change', args=[obj.client.pk])
        return format_html(
            '<a href="{}">'
            '<span class="cg-code">{}</span> '
            '<span class="cg-muted">{}</span>'
            '</a>',
            url, obj.client.client_code, obj.client.full_name[:16],
        )
    _client.short_description = _('Клиент')
    _client.admin_order_field = 'client__client_code'

    def _destination(self, obj):
        return obj.destination.code if obj.destination else '—'
    _destination.short_description = _('Направление')
    _destination.admin_order_field = 'destination__code'

    def _warehouse(self, obj):
        return obj.warehouse.code if obj.warehouse else '—'
    _warehouse.short_description = _('Склад')
    _warehouse.admin_order_field = 'warehouse__code'

    def _group(self, obj):
        if not obj.shipment_group:
            return format_html('<span class="cg-muted">—</span>')
        url = reverse('admin:shipments_shipmentgroup_change', args=[obj.shipment_group.pk])
        return format_html('<a href="{}" class="cg-code">{}</a>', url, obj.shipment_group.group_code)
    _group.short_description = _('Партия')
    _group.admin_order_field = 'shipment_group__group_code'

    def _weight(self, obj):
        return f'{obj.weight_kg} кг'
    _weight.short_description = _('Вес')
    _weight.admin_order_field = 'weight_kg'

    def _volume(self, obj):
        return f'{obj.volume_m3} м³'
    _volume.short_description = _('Объём')
    _volume.admin_order_field = 'volume_m3'

    def _total(self, obj):
        return money(obj.total_price, obj.declared_value_currency or '$')
    _total.short_description = _('Сумма')
    _total.admin_order_field = 'total_price'

    def _payment(self, obj):
        color, label = _PAYMENT.get(obj.payment_status, ('gray', obj.payment_status))
        return badge(label, color)
    _payment.short_description = _('Оплата')
    _payment.admin_order_field = 'payment_status'

    def _delivery(self, obj):
        color, label = _DELIVERY.get(obj.delivery_status, ('gray', obj.delivery_status))
        return badge(label, color)
    _delivery.short_description = _('Статус груза')
    _delivery.admin_order_field = 'delivery_status'

    def _stage(self, obj):
        color, label = _STAGE.get(obj.warehouse_stage, ('gray', obj.warehouse_stage))
        return badge(label, color)
    _stage.short_description = _('Этап склада')
    _stage.admin_order_field = 'warehouse_stage'

    def _created(self, obj):
        return obj.created_at.strftime('%d.%m.%Y') if obj.created_at else '—'
    _created.short_description = _('Дата создания')
    _created.admin_order_field = 'created_at'


# ── Supporting admins ──────────────────────────────────────────────────────────

@admin.register(ItemPhoto)
class ItemPhotoAdmin(ModelAdmin):
    list_display = ('id', 'item', 'file_name', '_size', 'uploaded_by', '_created')
    search_fields = ('item__item_code', 'file_name')
    list_filter = ('created_at', 'uploaded_by')
    list_select_related = ('item', 'uploaded_by')

    def _size(self, obj):
        if obj.file_size:
            return f'{obj.file_size // 1024} КБ'
        return '—'
    _size.short_description = _('Размер')

    def _created(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    _created.short_description = _('Дата загрузки')
    _created.admin_order_field = 'created_at'


@admin.register(Attachment)
class AttachmentAdmin(ModelAdmin):
    list_display = ('id', '_file_type', 'file_name', '_size', 'uploaded_by', '_created')
    list_filter = ('file_type', 'created_at', 'uploaded_by')
    search_fields = ('file_name', 'item__item_code', 'client__client_code', 'shipment_group__group_code')
    list_select_related = ('uploaded_by',)

    def _file_type(self, obj):
        return obj.get_file_type_display()
    _file_type.short_description = _('Тип файла')
    _file_type.admin_order_field = 'file_type'

    def _size(self, obj):
        if obj.file_size:
            return f'{obj.file_size // 1024} КБ'
        return '—'
    _size.short_description = _('Размер')

    def _created(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    _created.short_description = _('Дата загрузки')
    _created.admin_order_field = 'created_at'


@admin.register(ItemExpense)
class ItemExpenseAdmin(ModelAdmin):
    list_display = ('item', '_expense_type', '_amount', 'created_by', '_created')
    list_filter = ('expense_type', 'currency', 'created_at')
    search_fields = ('item__item_code', 'comment')
    list_select_related = ('item', 'created_by')

    def _expense_type(self, obj):
        return obj.get_expense_type_display()
    _expense_type.short_description = _('Тип расхода')
    _expense_type.admin_order_field = 'expense_type'

    def _amount(self, obj):
        return money(obj.amount, obj.currency)
    _amount.short_description = _('Сумма')
    _amount.admin_order_field = 'amount'

    def _created(self, obj):
        return obj.created_at.strftime('%d.%m.%Y')
    _created.short_description = _('Дата')
    _created.admin_order_field = 'created_at'


@admin.register(ItemStatusHistory)
class ItemStatusHistoryAdmin(ModelAdmin):
    list_display = ('item', '_old', '_new', 'changed_by', '_created')
    list_filter = ('old_status', 'new_status', 'changed_by', 'created_at')
    search_fields = ('item__item_code',)
    list_select_related = ('item', 'changed_by')

    def _old(self, obj):
        color, label = _DELIVERY.get(obj.old_status, ('gray', obj.old_status or '—'))
        return badge(label, color) if obj.old_status else '—'
    _old.short_description = _('Был')

    def _new(self, obj):
        color, label = _DELIVERY.get(obj.new_status, ('gray', obj.new_status))
        return badge(label, color)
    _new.short_description = _('Стал')

    def _created(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    _created.short_description = _('Дата изменения')
    _created.admin_order_field = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
