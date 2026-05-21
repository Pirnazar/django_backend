from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.locations.models import Destination, Warehouse
from apps.common.choices import CalculationType, Currency

class PriceRule(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='price_rules')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='price_rules', null=True, blank=True)
    name = models.CharField(max_length=150)
    calculation_type = models.CharField(max_length=20, choices=CalculationType.choices, default=CalculationType.WEIGHT)
    currency = models.CharField(max_length=10, choices=Currency.choices, default=Currency.USD)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    price_per_m3 = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fixed_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    min_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    extra_description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority']
        verbose_name = _('Тариф')
        verbose_name_plural = _('Тарифы')

    def __str__(self):
        return f"{self.name} - {self.destination.code}"
