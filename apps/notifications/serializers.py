"""Client-facing serializers for in-app notifications."""
from rest_framework import serializers

from .models import Notification, NotificationType, DeviceToken

_CARGO_TYPES = {
    NotificationType.ITEM_RECEIVED,
    NotificationType.ITEM_SENT,
    NotificationType.ITEM_ARRIVED,
    NotificationType.READY_FOR_PICKUP,
}


class ClientNotificationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    kind = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    body = serializers.SerializerMethodField()
    unread = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('id', 'kind', 'title', 'body', 'created_at', 'unread')

    def get_kind(self, obj):
        if obj.type in _CARGO_TYPES:
            return 'cargo'
        return 'system'

    def get_unread(self, obj):
        return obj.read_at is None

    def _localized(self, obj):
        """Re-localize to the app's current language (Accept-Language → client pref)."""
        from .i18n import localize, resolve_lang
        lang = resolve_lang(self.context.get('request'), obj.client)
        item_code = (obj.payload or {}).get('item_code', '')
        title, message = localize(obj.type, lang, item_code=item_code)
        if title is None:
            return obj.title, obj.message
        return title, message

    def get_title(self, obj):
        return self._localized(obj)[0]

    def get_body(self, obj):
        return self._localized(obj)[1]


class DeviceTokenSerializer(serializers.ModelSerializer):
    # Override to drop the auto UniqueValidator so registration is an upsert by token.
    token = serializers.CharField(max_length=512)

    class Meta:
        model = DeviceToken
        fields = ('token', 'platform', 'push_service', 'is_active')
        read_only_fields = ('is_active',)
