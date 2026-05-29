from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from .models import Client, AdditionalService, CargoService
from apps.items.models import Item
from apps.common.admin_helpers import badge, active_badge, RussianLabelsMixin, CLIENT_LABELS


class ItemInline(TabularInline):
    model = Item
    fields = ('item_code', 'weight_kg', 'volume_m3', 'payment_status', 'delivery_status', 'created_at')
    readonly_fields = ('item_code', 'weight_kg', 'volume_m3', 'payment_status', 'delivery_status', 'created_at')
    can_delete = False
    extra = 0
    show_change_link = True
    verbose_name = _('Груз клиента')
    verbose_name_plural = _('Последние грузы')

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')


@admin.action(description=_("Активировать выбранных клиентов"))
def activate_clients(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранных клиентов"))
def deactivate_clients(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(Client)
class ClientAdmin(RussianLabelsMixin, ModelAdmin):
    form_labels = CLIENT_LABELS
    warn_unsaved_changes = True
    show_full_result_count = False
    list_select_related = ('default_destination',)

    list_display = (
        '_code', '_name', '_phone',
        '_destination', '_active',
        '_items_count', '_created',
    )
    list_display_links = ('_code', '_name')
    list_filter = ('default_destination', 'is_active', 'created_at')
    search_fields = ('client_code', 'full_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    autocomplete_fields = ('default_destination',)
    ordering = ('-created_at',)

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('client_code', 'full_name', 'phone_number', 'default_destination'),
        }),
        (_('Контакты и профиль'), {
            'fields': ('whatsapp', 'wechat', 'preferred_language', 'delivery_city'),
        }),
        (_('Дополнительно'), {
            'fields': ('profile_photo', 'notes', 'is_active'),
        }),
        (_('Системная информация'), {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    actions = [activate_clients, deactivate_clients]
    inlines = [ItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_cnt=Count('items'))

    def _code(self, obj):
        return format_html('<span class="cg-code">{}</span>', obj.client_code)
    _code.short_description = _('Код клиента')
    _code.admin_order_field = 'client_code'

    def _name(self, obj):
        return obj.full_name
    _name.short_description = _('ФИО')
    _name.admin_order_field = 'full_name'

    def _phone(self, obj):
        return obj.phone_number or '—'
    _phone.short_description = _('Телефон')
    _phone.admin_order_field = 'phone_number'

    def _destination(self, obj):
        if obj.default_destination:
            return f'{obj.default_destination.code} — {obj.default_destination.name}'
        return '—'
    _destination.short_description = _('Направление')
    _destination.admin_order_field = 'default_destination__code'

    def _active(self, obj):
        return active_badge(obj.is_active)
    _active.short_description = _('Статус')
    _active.admin_order_field = 'is_active'

    def _items_count(self, obj):
        cnt = getattr(obj, '_cnt', 0)
        return cnt if cnt else '—'
    _items_count.short_description = _('Грузов')
    _items_count.admin_order_field = '_cnt'

    def _created(self, obj):
        return obj.created_at.strftime('%d.%m.%Y') if obj.created_at else '—'
    _created.short_description = _('Дата создания')
    _created.admin_order_field = 'created_at'


@admin.register(AdditionalService)
class AdditionalServiceAdmin(ModelAdmin):
    list_display = ('name', '_price', 'requires_comment', '_active')
    list_filter = ('is_active', 'currency', 'requires_comment')
    search_fields = ('name', 'description')
    ordering = ('name',)

    def _price(self, obj):
        return f'{obj.price} {obj.currency}'
    _price.short_description = _('Цена')

    def _active(self, obj):
        return active_badge(obj.is_active)
    _active.short_description = _('Активна')


_CARGO_SERVICE_STATUS = {
    'pending':     ('amber',  'Ожидает'),
    'in_progress': ('blue',   'В работе'),
    'done':        ('green',  'Выполнено'),
    'rejected':    ('red',    'Отклонено'),
    'cancelled':   ('gray',   'Отменено'),
}


@admin.register(CargoService)
class CargoServiceAdmin(ModelAdmin):
    list_display = ('_cargo', '_service', '_client', '_status', '_price', '_created')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('cargo__item_code', 'client__client_code', 'client__full_name', 'service__name')
    list_select_related = ('cargo', 'client', 'service')
    autocomplete_fields = ('cargo', 'client', 'service')
    ordering = ('-created_at',)

    def _cargo(self, obj):
        return obj.cargo.item_code if obj.cargo_id else '—'
    _cargo.short_description = _('Груз')

    def _service(self, obj):
        return obj.service.name if obj.service_id else '—'
    _service.short_description = _('Услуга')

    def _client(self, obj):
        return obj.client.client_code if obj.client_id else '—'
    _client.short_description = _('Клиент')

    def _status(self, obj):
        color, label = _CARGO_SERVICE_STATUS.get(obj.status, ('gray', obj.status))
        return badge(label, color)
    _status.short_description = _('Статус')
    _status.admin_order_field = 'status'

    def _price(self, obj):
        return f'{obj.price} {obj.currency}'
    _price.short_description = _('Цена')

    def _created(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M') if obj.created_at else '—'
    _created.short_description = _('Создано')
    _created.admin_order_field = 'created_at'
