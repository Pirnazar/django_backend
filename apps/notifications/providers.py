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


# ── Push providers (per-device) ───────────────────────────────────────────────
#
# Routing strategy (per the China/global split):
#   • Android в Китае  → JPush / GeTui / Umeng / Huawei (агрегатор покрывает OEM-каналы)
#   • Android Global   → Firebase FCM
#   • iOS              → Apple APNs (или JPush для iOS в Китае)
# Устройство само регистрируется с доступным сервисом (DeviceToken.push_service),
# а backend выбирает провайдера здесь. Конкретные SDK-вызовы — TODO с гейтом по настройкам.


class BasePushProvider:
    def send_push(self, notification, device) -> bool:
        raise NotImplementedError


class ConsolePushProvider(BasePushProvider):
    def send_push(self, notification, device) -> bool:
        logger.info(
            "PUSH [%s/%s] token=%s… → %s | %s",
            device.push_service, device.platform, str(device.token)[:12],
            notification.title, notification.message,
        )
        return True


class JPushProvider(BasePushProvider):
    """JPush 极光 — агрегатор для Китая (Huawei/Xiaomi/OPPO/Vivo/Honor + APNs-CN).

    TODO: интеграция через JPush REST API v3 (POST https://api.jpush.cn/v3/push),
    auth: base64(APP_KEY:MASTER_SECRET). Требует settings.JPUSH_APP_KEY / JPUSH_MASTER_SECRET.
    """
    def send_push(self, notification, device) -> bool:
        logger.warning("JPush не настроен — пропуск устройства %s", device.pk)
        return False


class FCMPushProvider(BasePushProvider):
    """Firebase FCM — Android Global. TODO: firebase-admin + FIREBASE_CREDENTIALS."""
    def send_push(self, notification, device) -> bool:
        logger.warning("FCM не настроен — пропуск устройства %s", device.pk)
        return False


class APNsPushProvider(BasePushProvider):
    """Apple APNs — iOS Global. TODO: APNs token-based auth (.p8 key)."""
    def send_push(self, notification, device) -> bool:
        logger.warning("APNs не настроен — пропуск устройства %s", device.pk)
        return False


_PUSH_REGISTRY = {
    'console': ConsolePushProvider,
    'fcm': FCMPushProvider,
    'apns': APNsPushProvider,
    'jpush': JPushProvider,
    # GeTui/Umeng/Huawei пока маршрутизируются на JPush-стиль агрегатор; заменить на свои при выборе
    'getui': JPushProvider,
    'umeng': JPushProvider,
    'huawei': JPushProvider,
}


def get_push_provider(device) -> BasePushProvider:
    provider_cls = _PUSH_REGISTRY.get(device.push_service, ConsolePushProvider)
    return provider_cls()
