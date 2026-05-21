from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import StaffUser
from apps.common.choices import StaffRole
from apps.common.admin_helpers import badge, active_badge, RussianLabelsMixin, STAFF_LABELS


_ROLE_COLORS = {
    StaffRole.SUPERADMIN: ('red',    'Суперадмин'),
    StaffRole.ADMIN:      ('violet', 'Администратор'),
    StaffRole.MANAGER:    ('blue',   'Менеджер'),
    StaffRole.OPERATOR:   ('teal',   'Оператор'),
    StaffRole.WAREHOUSE:  ('amber',  'Складской'),
}


@admin.register(StaffUser)
class StaffUserAdmin(RussianLabelsMixin, BaseUserAdmin, ModelAdmin):
    form_labels = STAFF_LABELS
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ('_full_name', '_email', '_phone', '_role', '_active', '_last_login', '_created_at')
    list_display_links = ('_full_name', '_email')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('full_name', 'email', 'phone_number')
    readonly_fields = ('last_login', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('email', 'full_name', 'phone_number', 'password'),
        }),
        (_('Доступ и роль'), {
            'fields': ('role', 'is_active', 'is_staff'),
        }),
        (_('Права и группы'), {
            'fields': ('is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('Даты'), {
            'fields': ('last_login', 'created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (_('Создать сотрудника'), {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'phone_number', 'role', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    def get_queryset(self, request):
        return StaffUser.all_objects.all()

    # ── Columns ────────────────────────────────────────────────────────────────

    def _full_name(self, obj):
        return obj.full_name
    _full_name.short_description = _('Полное имя')
    _full_name.admin_order_field = 'full_name'

    def _email(self, obj):
        return obj.email
    _email.short_description = _('Email')
    _email.admin_order_field = 'email'

    def _phone(self, obj):
        return obj.phone_number or '—'
    _phone.short_description = _('Телефон')
    _phone.admin_order_field = 'phone_number'

    def _role(self, obj):
        color, label = _ROLE_COLORS.get(obj.role, ('gray', obj.role))
        return badge(label, color)
    _role.short_description = _('Роль')
    _role.admin_order_field = 'role'

    def _active(self, obj):
        return active_badge(obj.is_active)
    _active.short_description = _('Активен')
    _active.admin_order_field = 'is_active'

    def _last_login(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%d.%m.%Y %H:%M')
        return '—'
    _last_login.short_description = _('Последний вход')
    _last_login.admin_order_field = 'last_login'

    def _created_at(self, obj):
        return obj.created_at.strftime('%d.%m.%Y') if obj.created_at else '—'
    _created_at.short_description = _('Дата создания')
    _created_at.admin_order_field = 'created_at'
