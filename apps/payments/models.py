from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.items.models import Item
from apps.clients.models import Client
from apps.common.choices import PaymentMethod, PaymentTransactionStatus, PaymentTransactionType

class PaymentTransaction(models.Model):
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    method = models.CharField(max_length=50, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    status = models.CharField(max_length=50, choices=PaymentTransactionStatus.choices, default=PaymentTransactionStatus.PENDING)
    transaction_type = models.CharField(max_length=50, choices=PaymentTransactionType.choices, default=PaymentTransactionType.PAYMENT)
    reference_number = models.CharField(max_length=100, blank=True)
    comment = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Платёж')
        verbose_name_plural = _('Платежи')

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency}"
