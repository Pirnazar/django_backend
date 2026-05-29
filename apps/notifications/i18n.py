"""Localization of notification text (ru / tk)."""
from .models import NotificationType

DEFAULT_LANG = 'ru'
SUPPORTED_LANGS = {'ru', 'tk'}

# type -> lang -> (title, message_template)
NOTIFICATION_TEXT = {
    NotificationType.ITEM_RECEIVED: {
        'ru': ('Груз принят', 'Ваш груз {item_code} принят на склад.'),
        'tk': ('Ýük kabul edildi', '{item_code} ýüküňiz ammara kabul edildi.'),
    },
    NotificationType.ITEM_SENT: {
        'ru': ('Груз отправлен', 'Ваш груз {item_code} отправлен в Туркменистан.'),
        'tk': ('Ýük ugradyldy', '{item_code} ýüküňiz Türkmenistana ugradyldy.'),
    },
    NotificationType.ITEM_ARRIVED: {
        'ru': ('Груз прибыл', 'Ваш груз {item_code} прибыл в Туркменистан.'),
        'tk': ('Ýük geldi', '{item_code} ýüküňiz Türkmenistana geldi.'),
    },
    NotificationType.READY_FOR_PICKUP: {
        'ru': ('Груз готов к выдаче', 'Ваш груз {item_code} готов к выдаче.'),
        'tk': ('Ýük almaga taýýar', '{item_code} ýüküňiz almaga taýýar.'),
    },
}


def normalize_lang(value):
    if not value:
        return None
    code = str(value).strip()[:2].lower()
    return code if code in SUPPORTED_LANGS else None


def resolve_lang(request=None, client=None):
    """Pick language: request Accept-Language → client.preferred_language → default."""
    if request is not None:
        header = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        code = normalize_lang(header.split(',')[0]) if header else None
        if code:
            return code
    if client is not None:
        code = normalize_lang(getattr(client, 'preferred_language', None))
        if code:
            return code
    return DEFAULT_LANG


def localize(notif_type, lang, **params):
    """Return (title, message) for a notification type in the given language."""
    table = NOTIFICATION_TEXT.get(notif_type)
    if not table:
        return None, None
    title, template = table.get(lang) or table.get(DEFAULT_LANG)
    try:
        message = template.format(**params)
    except (KeyError, IndexError):
        message = template
    return title, message
