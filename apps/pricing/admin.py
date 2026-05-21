from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from .models import PriceRule
from apps.common.choices import CalculationType
from apps.common.admin_helpers import badge, active_badge, money, RussianLabelsMixin, PRICE_LABELS


_CALC_COLORS = {
    CalculationType.WEIGHT: ('blue',   'За кг'),
    CalculationType.VOLUME: ('teal',   'За куб'),
    CalculationType.FIXED:  ('indigo', 'Фикс.'),
    CalculationType.MIXED:  ('violet', 'Смешанный'),
}


@admin.action(description=_("Активировать выбранные тарифы"))
def activate_tariffs(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description=_("Деактивировать выбранные тарифы"))
def deactivate_tariffs(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(PriceRule)
class PriceRuleAdmin(RussianLabelsMixin, ModelAdmin):
    form_labels = PRICE_LABELS
    list_select_related = ('destination', 'warehouse')

    list_display = (
        '_name', '_destination', '_warehouse',
        '_calc_type', '_currency',
        '_per_kg', '_per_m3', '_fixed', '_min',
        '_active', '_valid_from', '_valid_to', '_priority',
    )
    list_display_links = ('_name',)
    list_filter = ('destination', 'warehouse', 'calculation_type', 'currency', 'is_active')
    search_fields = ('name', 'destination__code', 'destination__name')
    autocomplete_fields = ('destination', 'warehouse')
    ordering = ('-priority',)
    actions = [activate_tariffs, deactivate_tariffs]

    fieldsets = (
        (_('Основное'), {
            'fields': ('name', 'destination', 'warehouse', 'is_active', 'priority'),
        }),
        (_('Расчёт'), {
            'fields': ('calculation_type', 'currency', 'price_per_kg', 'price_per_m3', 'fixed_price', 'min_charge'),
        }),
        (_('Срок действия'), {
            'fields': ('valid_from', 'valid_to'),
        }),
        (_('Описание'), {
            'fields': ('extra_description',),
            'classes': ('collapse',),
        }),
    )

    def _name(self, obj):
        return obj.name
    _name.short_description = _('Название')
    _name.admin_order_field = 'name'

    def _destination(self, obj):
        return obj.destination.code if obj.destination else '—'
    _destination.short_description = _('Направление')
    _destination.admin_order_field = 'destination__code'

    def _warehouse(self, obj):
        return obj.warehouse.code if obj.warehouse else '—'
    _warehouse.short_description = _('Склад')
    _warehouse.admin_order_field = 'warehouse__code'

    def _calc_type(self, obj):
        color, label = _CALC_COLORS.get(obj.calculation_type, ('gray', obj.calculation_type))
        return badge(label, color)
    _calc_type.short_description = _('Тип расчёта')
    _calc_type.admin_order_field = 'calculation_type'

    def _currency(self, obj):
        return obj.currency
    _currency.short_description = _('Валюта')
    _currency.admin_order_field = 'currency'

    def _per_kg(self, obj):
        return money(obj.price_per_kg, obj.currency) if obj.price_per_kg else '—'
    _per_kg.short_description = _('Цена/кг')
    _per_kg.admin_order_field = 'price_per_kg'

    def _per_m3(self, obj):
        return money(obj.price_per_m3, obj.currency) if obj.price_per_m3 else '—'
    _per_m3.short_description = _('Цена/м³')
    _per_m3.admin_order_field = 'price_per_m3'

    def _fixed(self, obj):
        return money(obj.fixed_price, obj.currency) if obj.fixed_price else '—'
    _fixed.short_description = _('Фикс. цена')
    _fixed.admin_order_field = 'fixed_price'

    def _min(self, obj):
        return money(obj.min_charge, obj.currency) if obj.min_charge else '—'
    _min.short_description = _('Мин. сумма')
    _min.admin_order_field = 'min_charge'

    def _active(self, obj):
        return active_badge(obj.is_active)
    _active.short_description = _('Активен')
    _active.admin_order_field = 'is_active'

    def _valid_from(self, obj):
        return obj.valid_from.strftime('%d.%m.%Y') if obj.valid_from else '—'
    _valid_from.short_description = _('Действует с')
    _valid_from.admin_order_field = 'valid_from'

    def _valid_to(self, obj):
        return obj.valid_to.strftime('%d.%m.%Y') if obj.valid_to else '—'
    _valid_to.short_description = _('Действует до')
    _valid_to.admin_order_field = 'valid_to'

    def _priority(self, obj):
        return obj.priority
    _priority.short_description = _('Приоритет')
    _priority.admin_order_field = 'priority'
