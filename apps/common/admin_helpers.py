from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# (color_name) → CSS class suffix
_COLORS = {
    'green', 'red', 'amber', 'blue', 'sky', 'gray',
    'cyan', 'indigo', 'orange', 'violet', 'teal', 'purple',
}


def badge(text, color='gray'):
    if color not in _COLORS:
        color = 'gray'
    return format_html(
        '<span class="cg-badge cg-badge-{}">{}</span>',
        color, text,
    )


def money(amount, currency='$'):
    if amount is None or amount == 0:
        return format_html('<span class="cg-money-zero">—</span>')
    formatted = f'{amount:,.2f}'.replace(',', ' ')
    return format_html('<span class="cg-money">{}&nbsp;{}</span>', formatted, currency)


def active_badge(is_active):
    if is_active:
        return badge('Активен', 'green')
    return badge('Неактивен', 'gray')


def photo_preview(file_field, max_px=80):
    if file_field:
        return format_html(
            '<img src="{}" class="cg-photo-preview" style="max-height:{}px;max-width:{}px;" />',
            file_field.url, max_px, max_px,
        )
    return '—'


class RussianLabelsMixin:
    """
    Mixin for ModelAdmin: overrides form field labels with Russian text.
    Define `form_labels = {'field_name': _('Русский')}` in the subclass.
    """
    form_labels: dict = {}

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for field_name, label in self.form_labels.items():
            if field_name in form.base_fields:
                form.base_fields[field_name].label = label
        return form


# ── Common label dictionaries (reused across admins) ──────────────────────────

COMMON_LABELS = {
    'comment':    _('Комментарий'),
    'description': _('Описание'),
    'created_at': _('Дата создания'),
    'updated_at': _('Дата обновления'),
    'deleted_at': _('Дата удаления'),
    'created_by': _('Создал'),
    'updated_by': _('Обновил'),
    'is_active':  _('Активен'),
}

ITEM_LABELS = {
    **COMMON_LABELS,
    'item_code':              _('Код груза'),
    'barcode':                _('Штрихкод'),
    'qr_code':                _('QR-код'),
    'express_code':           _('Экспресс-код'),
    'item_type':              _('Тип груза'),
    'transport_type':         _('Тип перевозки'),
    'place_count':            _('Кол-во мест'),
    'client':                 _('Клиент'),
    'destination':            _('Направление'),
    'warehouse':              _('Склад'),
    'shipment_group':         _('Партия'),
    'price_rule':             _('Тариф'),
    'weight_kg':              _('Вес (кг)'),
    'length_cm':              _('Длина (см)'),
    'width_cm':               _('Ширина (см)'),
    'height_cm':              _('Высота (см)'),
    'volume_source':          _('Источник объёма'),
    'volume_m3':              _('Объём (м³)'),
    'declared_value':         _('Заявленная стоимость'),
    'declared_value_currency':_('Валюта стоимости'),
    'calculated_price':       _('Расчётная цена'),
    'external_expenses_total':_('Доп. расходы'),
    'total_price':            _('Итого'),
    'payment_type':           _('Тип оплаты'),
    'payment_status':         _('Статус оплаты'),
    'delivery_status':        _('Статус доставки'),
    'warehouse_stage':        _('Этап склада'),
    'is_fragile':             _('Хрупкий'),
    'has_battery':            _('Содержит батарею'),
    'is_repacked':            _('Перепакован'),
    'is_dangerous':           _('Опасный'),
    'requires_manual_review': _('Требует проверки'),
}

SHIPMENT_LABELS = {
    **COMMON_LABELS,
    'group_code':                  _('Код партии'),
    'destination':                 _('Направление'),
    'warehouse':                   _('Склад'),
    'status':                      _('Статус'),
    'total_items':                 _('Кол-во грузов'),
    'total_weight_kg':             _('Общий вес (кг)'),
    'total_volume_m3':             _('Общий объём (м³)'),
    'sent_to_urumqi_date':         _('Отправлен в Урумчи'),
    'arrived_urumqi_date':         _('Прибыл в Урумчи'),
    'sent_to_turkmenistan_date':   _('Отправлен в ТМ'),
    'arrived_turkmenistan_date':   _('Прибыл в ТМ'),
    'china_to_urumqi_cost':        _('Стоимость Китай → Урумчи'),
    'china_to_turkmenistan_cost':  _('Стоимость Китай → ТМ'),
}

CLIENT_LABELS = {
    **COMMON_LABELS,
    'client_code':        _('Код клиента'),
    'full_name':          _('ФИО'),
    'phone_number':       _('Телефон'),
    'default_destination':_('Направление'),
    'profile_photo':      _('Фото профиля'),
    'notes':              _('Заметки'),
}

STAFF_LABELS = {
    **COMMON_LABELS,
    'email':          _('Email'),
    'full_name':      _('Полное имя'),
    'phone_number':   _('Телефон'),
    'password':       _('Пароль'),
    'password1':      _('Пароль'),
    'password2':      _('Подтверждение пароля'),
    'role':           _('Роль'),
    'is_staff':       _('Доступ к admin'),
    'is_superuser':   _('Суперпользователь'),
    'groups':         _('Группы'),
    'user_permissions': _('Права пользователя'),
    'last_login':     _('Последний вход'),
    'deleted_at':     _('Дата удаления'),
}

PAYMENT_LABELS = {
    **COMMON_LABELS,
    'item':               _('Груз'),
    'client':             _('Клиент'),
    'amount':             _('Сумма'),
    'currency':           _('Валюта'),
    'method':             _('Метод оплаты'),
    'status':             _('Статус'),
    'transaction_type':   _('Тип транзакции'),
    'paid_at':            _('Дата оплаты'),
    'reference_number':   _('Номер ссылки'),
}

PRICE_LABELS = {
    **COMMON_LABELS,
    'name':             _('Название'),
    'destination':      _('Направление'),
    'warehouse':        _('Склад'),
    'calculation_type': _('Тип расчёта'),
    'currency':         _('Валюта'),
    'price_per_kg':     _('Цена за кг'),
    'price_per_m3':     _('Цена за м³'),
    'fixed_price':      _('Фикс. цена'),
    'min_charge':       _('Мин. сумма'),
    'extra_description':_('Описание'),
    'valid_from':       _('Действует с'),
    'valid_to':         _('Действует до'),
    'priority':         _('Приоритет'),
}

DESTINATION_LABELS = {
    'code':         _('Код'),
    'name':         _('Название'),
    'country_name': _('Страна'),
    'is_active':    _('Активно'),
}

WAREHOUSE_LABELS = {
    'code':    _('Код'),
    'name':    _('Название'),
    'country': _('Страна'),
    'city':    _('Город'),
    'address': _('Адрес'),
    'is_active': _('Активен'),
}
