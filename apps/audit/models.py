from django.db import models
from django.utils.translation import gettext_lazy as _

class AuditLog(models.Model):
    actor = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    action = models.CharField(max_length=50)
    old_data = models.JSONField(null=True, blank=True)
    new_data = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Журнал действий')
        verbose_name_plural = _('Журнал действий')

    def __str__(self):
        return f"{self.actor} - {self.action} - {self.entity_type} ({self.entity_id})"
