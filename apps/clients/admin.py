from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from .models import Client
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
