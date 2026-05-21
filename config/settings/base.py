import os
from pathlib import Path
from datetime import timedelta
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key')

DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

INSTALLED_APPS = [
    "unfold",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    
    # Local
    'apps.accounts',
    'apps.common',
    'apps.locations',
    'apps.clients',
    'apps.pricing',
    'apps.shipments',
    'apps.items',
    'apps.payments',
    'apps.audit',
    'apps.dashboard',
    'apps.notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://postgres:postgres@localhost:5432/cargo_db')
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru'
LANGUAGES = [('ru', 'Русский')]
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.StaffUser'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Cargo Warehouse CRM API',
    'DESCRIPTION': 'Logistics and Warehouse System API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
    }
}

from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": _("Ýyldyrym Cargo"),
    "SITE_HEADER": _("Ýyldyrym Cargo"),
    "SITE_SYMBOL": "bolt",
    "SITE_LOGO": {
        "light": lambda request: "/static/img/logo.png",
        "dark": lambda request: "/static/img/logo.png",
    },
    "STYLES": [
        lambda request: "/static/css/custom_admin.css",
    ],
    "DASHBOARD_CALLBACK": "apps.dashboard.admin_dashboard.dashboard_callback",
    "COLORS": {
        "primary": {
            "50":  "239 246 255",
            "100": "219 234 254",
            "200": "191 219 254",
            "300": "147 197 253",
            "400": "96 165 250",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Главная"),
                "separator": True,
                "items": [
                    {
                        "title": _("Панель управления"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index") if 'reverse_lazy' in globals() else "/",
                    },
                ],
            },
            {
                "title": _("Операции"),
                "separator": True,
                "items": [
                    {
                        "title": _("Грузы"),
                        "icon": "inventory_2",
                        "link": reverse_lazy("admin:items_item_changelist") if 'reverse_lazy' in globals() else "/admin/items/item/",
                    },
                    {
                        "title": _("Партии"),
                        "icon": "local_shipping",
                        "link": reverse_lazy("admin:shipments_shipmentgroup_changelist") if 'reverse_lazy' in globals() else "/admin/shipments/shipmentgroup/",
                    },
                    {
                        "title": _("Платежи"),
                        "icon": "payments",
                        "link": reverse_lazy("admin:payments_paymenttransaction_changelist") if 'reverse_lazy' in globals() else "/admin/payments/paymenttransaction/",
                    },
                    {
                        "title": _("Конструктор партии"),
                        "icon": "build_circle",
                        "link": "/admin/shipment-group-builder/",
                    },
                    {
                        "title": _("Коробки"),
                        "icon": "package_2",
                        "link": reverse_lazy("admin:items_box_changelist") if 'reverse_lazy' in globals() else "/admin/items/box/",
                    },
                    {
                        "title": _("Конструктор коробки"),
                        "icon": "package_2",
                        "link": "/admin/box-builder/",
                    },
                ],
            },
            {
                "title": _("Уведомления"),
                "separator": True,
                "items": [
                    {
                        "title": _("Уведомления клиентам"),
                        "icon": "notifications",
                        "link": reverse_lazy("admin:notifications_notification_changelist") if 'reverse_lazy' in globals() else "/admin/notifications/notification/",
                    },
                ],
            },
            {
                "title": _("Справочники"),
                "separator": True,
                "items": [
                    {
                        "title": _("Клиенты"),
                        "icon": "groups",
                        "link": reverse_lazy("admin:clients_client_changelist") if 'reverse_lazy' in globals() else "/admin/clients/client/",
                    },
                    {
                        "title": _("Направления"),
                        "icon": "map",
                        "link": reverse_lazy("admin:locations_destination_changelist") if 'reverse_lazy' in globals() else "/admin/locations/destination/",
                    },
                    {
                        "title": _("Склады"),
                        "icon": "warehouse",
                        "link": reverse_lazy("admin:locations_warehouse_changelist") if 'reverse_lazy' in globals() else "/admin/locations/warehouse/",
                    },
                    {
                        "title": _("Тарифы"),
                        "icon": "sell",
                        "link": reverse_lazy("admin:pricing_pricerule_changelist") if 'reverse_lazy' in globals() else "/admin/pricing/pricerule/",
                    },
                ],
            },
            {
                "title": _("Файлы"),
                "separator": True,
                "items": [
                    {
                        "title": _("Фото грузов"),
                        "icon": "photo_camera",
                        "link": reverse_lazy("admin:items_itemphoto_changelist") if 'reverse_lazy' in globals() else "/admin/items/itemphoto/",
                    },
                    {
                        "title": _("Вложения"),
                        "icon": "attach_file",
                        "link": reverse_lazy("admin:items_attachment_changelist") if 'reverse_lazy' in globals() else "/admin/items/attachment/",
                    },
                ],
            },
            {
                "title": _("Сотрудники и доступ"),
                "separator": True,
                "items": [
                    {
                        "title": _("Сотрудники"),
                        "icon": "manage_accounts",
                        "link": reverse_lazy("admin:accounts_staffuser_changelist") if 'reverse_lazy' in globals() else "/admin/accounts/staffuser/",
                    },
                ],
            },
            {
                "title": _("Мониторинг"),
                "separator": True,
                "items": [
                    {
                        "title": _("Журнал действий"),
                        "icon": "history",
                        "link": reverse_lazy("admin:audit_auditlog_changelist") if 'reverse_lazy' in globals() else "/admin/audit/auditlog/",
                    },
                    {
                        "title": _("История грузов"),
                        "icon": "history",
                        "link": reverse_lazy("admin:items_itemstatushistory_changelist") if 'reverse_lazy' in globals() else "/admin/items/itemstatushistory/",
                    },
                    {
                        "title": _("История партий"),
                        "icon": "history",
                        "link": reverse_lazy("admin:shipments_shipmentgroupstatushistory_changelist") if 'reverse_lazy' in globals() else "/admin/shipments/shipmentgroupstatushistory/",
                    },
                ],
            },
        ],
    },
}
