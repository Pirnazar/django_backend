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
