from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.models import TimeStampedSoftDeleteModel

class Destination(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    country_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Направление')
        verbose_name_plural = _('Направления')

    def __str__(self):
        return f"{self.code} - {self.name}"

class Warehouse(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Склад')
        verbose_name_plural = _('Склады')

    def __str__(self):
        return f"{self.name} ({self.code})"
