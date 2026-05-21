import logging

logger = logging.getLogger(__name__)


class BaseNotificationProvider:
    def send(self, notification) -> bool:
        raise NotImplementedError


class ConsoleNotificationProvider(BaseNotificationProvider):
    def send(self, notification) -> bool:
        logger.info(
            "NOTIFICATION [%s/%s] → %s (%s): %s",
            notification.channel,
            notification.type,
            notification.client,
            getattr(notification.client, 'phone_number', '—'),
            notification.message,
        )
        return True


def get_provider(channel) -> BaseNotificationProvider:
    return ConsoleNotificationProvider()
