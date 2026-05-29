from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.common.models import TimeStampedSoftDeleteModel
from apps.locations.models import Destination

class Client(TimeStampedSoftDeleteModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_profile')
    client_code = models.CharField(max_length=50, unique=True, db_index=True, blank=True)
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True, db_index=True)
    default_destination = models.ForeignKey(Destination, null=True, blank=True, on_delete=models.SET_NULL, related_name='clients')
    profile_photo = models.ImageField(upload_to='clients/photos/', null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    # Контактные/профильные поля для мобильного приложения
    whatsapp = models.CharField(_('WhatsApp'), max_length=30, blank=True)
    wechat = models.CharField(_('WeChat'), max_length=50, blank=True)
    preferred_language = models.CharField(_('Язык'), max_length=10, blank=True)
    delivery_city = models.CharField(_('Город доставки'), max_length=100, blank=True)

    class Meta:
        verbose_name = _('Клиент')
        verbose_name_plural = _('Клиенты')

    def __str__(self):
        parts = [self.client_code, self.full_name]
        if self.phone_number:
            parts.append(self.phone_number)
        return " — ".join(parts)

    def clean(self):
        super().clean()
        if self.client_code:
            self.client_code = self.client_code.strip()
            if any(c.isalpha() for c in self.client_code):
                self.client_code = self.client_code.upper()
            
            from django.core.exceptions import ValidationError
            qs = Client.objects.filter(client_code=self.client_code)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"client_code": _("Клиент с таким кодом уже существует")})

    def save(self, *args, **kwargs):
        if not self.client_code:
            from apps.common.services import generate_client_code
            self.client_code = generate_client_code()
        else:
            self.client_code = self.client_code.strip()
            if any(c.isalpha() for c in self.client_code):
                self.client_code = self.client_code.upper()
        super().save(*args, **kwargs)


class AdditionalService(TimeStampedSoftDeleteModel):
    """Catalogue of extra services a client can request for a cargo."""
    name = models.CharField(_('Название'), max_length=150)
    description = models.TextField(_('Описание'), blank=True)
    price = models.DecimalField(_('Цена'), max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(_('Валюта'), max_length=10, default='USD')
    requires_comment = models.BooleanField(_('Требует комментарий'), default=False)
    is_active = models.BooleanField(_('Активна'), default=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Доп. услуга')
        verbose_name_plural = _('Доп. услуги')

    def __str__(self):
        return self.name


class CargoServiceStatus(models.TextChoices):
    PENDING     = 'pending',     _('Ожидает')
    IN_PROGRESS = 'in_progress', _('В работе')
    DONE        = 'done',        _('Выполнено')
    REJECTED    = 'rejected',    _('Отклонено')
    CANCELLED   = 'cancelled',   _('Отменено')


class CargoService(TimeStampedSoftDeleteModel):
    """A service requested by a client for a specific cargo (Item)."""
    cargo = models.ForeignKey('items.Item', on_delete=models.CASCADE, related_name='requested_services')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='requested_services')
    service = models.ForeignKey(AdditionalService, on_delete=models.PROTECT, related_name='requests')
    status = models.CharField(max_length=20, choices=CargoServiceStatus.choices, default=CargoServiceStatus.PENDING)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Запрос услуги')
        verbose_name_plural = _('Запросы услуг')

    def __str__(self):
        return f'{self.service.name} → {self.cargo_id} [{self.get_status_display()}]'
