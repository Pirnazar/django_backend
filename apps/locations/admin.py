from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from .models import Destination, Warehouse
from apps.common.admin_helpers import active_badge, RussianLabelsMixin, DESTINATION_LABELS, WAREHOUSE_LABELS


@admin.register(Destination)
class DestinationAdmin(RussianLabelsMixin, ModelAdmin):
    form_labels = DESTINATION_LABELS
    list_display = ('_code', '_name', '_country', '_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name', 'country_name')
    ordering = ('code',)

    fieldsets = (
        (_('Направление'), {
            'fields': ('code', 'name', 'country_name', 'is_active'),
        }),
    )

    def _code(self, obj):
        return obj.code
    _code.short_description = _('Код')
    _code.admin_order_field = 'code'

    def _name(self, obj):
        return obj.name
    _name.short_description = _('Название')
    _name.admin_order_field = 'name'

    def _country(self, obj):
        return obj.country_name or '—'
    _country.short_description = _('Страна')
    _country.admin_order_field = 'country_name'

    def _active(self, obj):
        return active_badge(obj.is_active)
    _active.short_description = _('Статус')
    _active.admin_order_field = 'is_active'


@admin.register(Warehouse)
class WarehouseAdmin(RussianLabelsMixin, ModelAdmin):
    form_labels = WAREHOUSE_LABELS
    list_display = ('_code', '_name', '_country', '_city', '_active')
    list_filter = ('country', 'city', 'is_active')
    search_fields = ('code', 'name', 'city', 'address')
    ordering = ('code',)

    fieldsets = (
        (_('Основное'), {
            'fields': ('code', 'name', 'is_active'),
        }),
        (_('Адрес'), {
            'fields': ('country', 'city', 'address'),
        }),
    )

    def _code(self, obj):
        return obj.code
    _code.short_description = _('Код')
    _code.admin_order_field = 'code'

    def _name(self, obj):
        return obj.name
    _name.short_description = _('Название')
    _name.admin_order_field = 'name'

    def _country(self, obj):
        return obj.country
    _country.short_description = _('Страна')
    _country.admin_order_field = 'country'

    def _city(self, obj):
        return obj.city
    _city.short_description = _('Город')
    _city.admin_order_field = 'city'

    def _active(self, obj):
        return active_badge(obj.is_active)
    _active.short_description = _('Статус')
    _active.admin_order_field = 'is_active'
