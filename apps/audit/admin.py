from django.contrib import admin
import json
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from .models import AuditLog
from apps.common.admin_helpers import badge


_ACTION_MAP = {
    'CREATE': ('green',  'Создан'),
    'UPDATE': ('amber',  'Изменён'),
    'DELETE': ('red',    'Удалён'),
}


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ('_action', '_entity_type', '_entity_id', '_actor', '_ip', '_created')
    list_filter = ('entity_type', 'action', 'actor', 'created_at')
    search_fields = ('entity_type', 'entity_id', 'action', 'actor')
    readonly_fields = (
        'actor', 'action', 'entity_type', 'entity_id',
        'ip_address', 'user_agent',
        '_old_data', '_new_data',
        'created_at',
    )
    exclude = ('old_data', 'new_data')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        (_('Событие'), {
            'fields': ('actor', 'action', 'entity_type', 'entity_id', 'ip_address', 'user_agent', 'created_at'),
        }),
        (_('Данные до'), {
            'fields': ('_old_data',),
        }),
        (_('Данные после'), {
            'fields': ('_new_data',),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def _action(self, obj):
        color, label = _ACTION_MAP.get(obj.action, ('gray', obj.action))
        return badge(label, color)
    _action.short_description = _('Действие')
    _action.admin_order_field = 'action'

    def _entity_type(self, obj):
        return obj.entity_type
    _entity_type.short_description = _('Тип объекта')
    _entity_type.admin_order_field = 'entity_type'

    def _entity_id(self, obj):
        return obj.entity_id
    _entity_id.short_description = _('ID объекта')
    _entity_id.admin_order_field = 'entity_id'

    def _actor(self, obj):
        return obj.actor or '—'
    _actor.short_description = _('Пользователь')
    _actor.admin_order_field = 'actor'

    def _ip(self, obj):
        return obj.ip_address or '—'
    _ip.short_description = _('IP-адрес')
    _ip.admin_order_field = 'ip_address'

    def _created(self, obj):
        return obj.created_at.strftime('%d.%m.%Y %H:%M')
    _created.short_description = _('Дата')
    _created.admin_order_field = 'created_at'

    def _old_data(self, obj):
        return self._render_json(obj.old_data)
    _old_data.short_description = _('Старые данные')

    def _new_data(self, obj):
        return self._render_json(obj.new_data)
    _new_data.short_description = _('Новые данные')

    @staticmethod
    def _render_json(data):
        if not data:
            return format_html('<span style="color:#9CA3AF">—</span>')
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        return format_html('<pre class="cg-json-block">{}</pre>', formatted)
