from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from .models import ShipmentGroup, ShipmentGroupStatusHistory
from apps.items.models import Item, Attachment
from apps.common.choices import ShipmentGroupStatus
from apps.common.admin_helpers import badge, RussianLabelsMixin, SHIPMENT_LABELS


# ── Status colour map ──────────────────────────────────────────────────────────

_GROUP_STATUS = {
    ShipmentGroupStatus.DRAFT:                      ('gray',   'Черновик'),
    ShipmentGroupStatus.FORMING:                    ('amber',  'Формируется'),
    ShipmentGroupStatus.READY_TO_DISPATCH:          ('blue',   'Готов к отправке'),
    ShipmentGroupStatus.IN_TRANSIT_TO_URUMQI:       ('orange', 'В пути → Урумчи'),
    ShipmentGroupStatus.ARRIVED_URUMQI:             ('teal',   'Прибыл Урумчи'),
    ShipmentGroupStatus.IN_TRANSIT_TO_TURKMENISTAN: ('orange', 'В пути → ТМ'),
    ShipmentGroupStatus.ARRIVED_TURKMENISTAN:       ('teal',   'Прибыл в ТМ'),
    ShipmentGroupStatus.COMPLETED:                  ('green',  'Завершена'),
    ShipmentGroupStatus.CANCELLED:                  ('red',    'Отменена'),
}


# ── Inlines ────────────────────────────────────────────────────────────────────

class GroupItemInline(TabularInline):
    model = Item
    fields = ('item_code', 'weight_kg', 'volume_m3', 'payment_status', 'delivery_status', 'created_at')
    readonly_fields = ('item_code', 'weight_kg', 'volume_m3', 'payment_status', 'delivery_status', 'created_at')
    can_delete = False
    extra = 0
    verbose_name = _('Груз в партии')
    verbose_name_plural = _('Грузы в партии')
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


class ShipmentGroupStatusHistoryInline(TabularInline):
    model = ShipmentGroupStatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'comment', 'changed_by', 'created_at')
    can_delete = False
    verbose_name = _('Запись')
    verbose_name_plural = _('История статусов')

    def has_add_permission(self, request, obj=None):
        return False


class GroupAttachmentInline(TabularInline):
    model = Attachment
    extra = 0
    fields = ('file_type', 'file', 'file_name', 'file_size', 'uploaded_by', 'created_at')
    readonly_fields = ('file_size', 'uploaded_by', 'created_at')
    verbose_name = _('Вложение')
    verbose_name_plural = _('Вложения партии')


# ── Bulk actions ───────────────────────────────────────────────────────────────

@admin.action(description=_("Пересчитать итоги партий"))
def recalculate_group_totals(modeladmin, request, queryset):
    from apps.shipments.services import recalculate_shipment_group_totals
    for group in queryset:
        recalculate_shipment_group_totals(group)


@admin.action(description=_("Отметить 'Готов к отправке'"))
def mark_ready(modeladmin, request, queryset):
    queryset.update(status=ShipmentGroupStatus.READY_TO_DISPATCH)


@admin.action(description=_("Отметить 'В пути → Урумчи'"))
def mark_transit_urumqi(modeladmin, request, queryset):
    queryset.update(status=ShipmentGroupStatus.IN_TRANSIT_TO_URUMQI)


@admin.action(description=_("Отметить 'В пути → ТМ'"))
def mark_transit_tm(modeladmin, request, queryset):
    queryset.update(status=ShipmentGroupStatus.IN_TRANSIT_TO_TURKMENISTAN)


@admin.action(description=_("Отметить 'Прибыл в ТМ'"))
def mark_arrived_tm(modeladmin, request, queryset):
    queryset.update(status=ShipmentGroupStatus.ARRIVED_TURKMENISTAN)


@admin.action(description=_("Отметить 'Завершена'"))
def mark_completed(modeladmin, request, queryset):
    queryset.update(status=ShipmentGroupStatus.COMPLETED)


# ── Main admin ─────────────────────────────────────────────────────────────────

@admin.register(ShipmentGroup)
class ShipmentGroupAdmin(RussianLabelsMixin, ModelAdmin):
    form_labels = SHIPMENT_LABELS
    warn_unsaved_changes = True
    show_full_result_count = False
    list_select_related = ('destination', 'warehouse')

    list_display = (
        '_code', '_destination', '_warehouse',
        '_items', '_weight', '_volume',
        '_status',
        '_sent_ur', '_arr_tm',
        '_created',
    )
    list_display_links = ('_code',)
    list_filter = ('destination', 'warehouse', 'status', 'created_at')
    search_fields = ('group_code', 'destination__code', 'destination__name')
    readonly_fields = (
        'group_code', 'total_items', 'total_weight_kg', 'total_volume_m3',
        'created_at', 'updated_at',
    )
    autocomplete_fields = ('destination', 'warehouse')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        (_('Основные данные'), {
            'fields': ('group_code', 'destination', 'warehouse', 'status', 'comment'),
        }),
        (_('Итоги'), {
            'fields': ('total_items', 'total_weight_kg', 'total_volume_m3'),
        }),
        (_('Даты'), {
            'fields': (
                'sent_to_urumqi_date', 'arrived_urumqi_date',
                'sent_to_turkmenistan_date', 'arrived_turkmenistan_date',
            ),
        }),
        (_('Стоимость перевозки'), {
            'fields': ('china_to_urumqi_cost', 'china_to_turkmenistan_cost'),
        }),
        (_('Системная информация'), {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    inlines = [GroupItemInline, ShipmentGroupStatusHistoryInline, GroupAttachmentInline]
    actions = [
        recalculate_group_totals, mark_ready, mark_transit_urumqi,
        mark_transit_tm, mark_arrived_tm, mark_completed,
    ]

    def _code(self, obj):
        return format_html('<span class="cg-code">{}</span>', obj.group_code)
    _code.short_description = _('Код партии')
    _code.admin_order_field = 'group_code'

    def _destination(self, obj):
        return obj.destination.code if obj.destination else '—'
    _destination.short_description = _('Направление')
    _destination.admin_order_field = 'destination__code'

    def _warehouse(self, obj):
        return obj.warehouse.code if obj.warehouse else '—'
    _warehouse.short_description = _('Склад')
    _warehouse.admin_order_field = 'warehouse__code'

    def _items(self, obj):
        return obj.total_items
    _items.short_description = _('Грузов')
    _items.admin_order_field = 'total_items'

    def _weight(self, obj):
        return f'{obj.total_weight_kg} кг'
    _weight.short_description = _('Вес')
    _weight.admin_order_field = 'total_weight_kg'

    def _volume(self, obj):
        return f'{obj.total_volume_m3} м³'
    _volume.short_description = _('Объём')
    _volume.admin_order_field = 'total_volume_m3'

    def _status(self, obj):
        color, label = _GROUP_STATUS.get(obj.status, ('gray', obj.status))
        return badge(label, color)
    _status.short_description = _('Статус')
    _status.admin_order_field = 'status'

    def _sent_ur(self, obj):
        if obj.sent_to_urumqi_date:
            return obj.sent_to_urumqi_date.strftime('%d.%m.%Y')
        return format_html('<span class="cg-muted">—</span>')
    _sent_ur.short_description = _('Отправлен в Урумчи')
    _sent_ur.admin_order_field = 'sent_to_urumqi_date'

    def _arr_tm(self, obj):
        if obj.arrived_turkmenistan_date:
            return obj.arrived_turkmenistan_date.strftime('%d.%m.%Y')
        return format_html('<span class="cg-muted">—</span>')
    _arr_tm.short_description = _('Прибыл в ТМ')
    _arr_tm.admin_order_field = 'arrived_turkmenistan_date'

    def _created(self, obj):
        return obj.created_at.strftime('%d.%m.%Y') if obj.created_at else '—'
    _created.short_description = _('Дата создания')
    _created.admin_order_field = 'created_at'


# ── Supporting admin ───────────────────────────────────────────────────────────

@admin.register(ShipmentGroupStatusHistory)
class ShipmentGroupStatusHistoryAdmin(ModelAdmin):
    list_display = ('shipment_group', '_old', '_new', 'changed_by', '_created')
    list_filter = ('old_status', 'new_status', 'changed_by', 'created_at')
    search_fields = ('shipment_group__group_code',)
    list_select_related = ('shipment_group', 'changed_by')

    def _old(self, obj):
        color, label = _GROUP_STATUS.get(obj.old_status, ('gray', obj.old_status or '—'))
        return badge(label, color) if obj.old_status else '—'
    _old.short_description = _('Был')

    def _new(self, obj):
        color, label = _GROUP_STATUS.get(obj.new_status, ('gray', obj.new_status))
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
