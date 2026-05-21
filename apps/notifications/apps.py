from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = 'apps.notifications'
    verbose_name = 'Уведомления'

    def ready(self):
        import apps.notifications.signals  # noqa
