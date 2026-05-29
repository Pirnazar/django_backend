from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.common.models import TimeStampedSoftDeleteModel
from apps.clients.models import Client
from apps.locations.models import Destination, Warehouse
from apps.shipments.models import ShipmentGroup
from apps.pricing.models import PriceRule
from apps.common.choices import (
    ItemType, TransportType, PaymentType, PaymentStatus,
    DeliveryStatus, WarehouseStage, ExpenseType, VolumeSource, AttachmentType,
)


class Item(TimeStampedSoftDeleteModel):
    item_code = models.CharField(max_length=50, unique=True, db_index=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='items')
    destination = models.ForeignKey(Destination, on_delete=models.PROTECT, related_name='items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='items')
    shipment_group = models.ForeignKey(ShipmentGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    price_rule = models.ForeignKey(PriceRule, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    
    barcode = models.CharField(max_length=100, blank=True, db_index=True)
    qr_code = models.CharField(max_length=255, blank=True)
    express_code = models.CharField(max_length=100, blank=True, db_index=True)
    
    main_photo = models.ImageField(upload_to='items/main_photos/', null=True, blank=True, verbose_name=_("Основное фото (коллаж)"))
    
    item_type = models.CharField(max_length=50, choices=ItemType.choices, default=ItemType.STANDARD)
    transport_type = models.CharField(max_length=50, choices=TransportType.choices, default=TransportType.AUTO)
    
    place_count = models.IntegerField(default=1)
    weight_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    length_cm = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    width_cm = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    height_cm = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    volume_m3 = models.DecimalField(max_digits=10, decimal_places=4, default=0.0000)
    volume_source = models.CharField(max_length=20, choices=VolumeSource.choices, default=VolumeSource.CALCULATED)
    
    declared_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    declared_value_currency = models.CharField(max_length=10, default='USD')
    
    payment_type = models.CharField(max_length=50, choices=PaymentType.choices, default=PaymentType.WEIGHT)
    payment_status = models.CharField(max_length=50, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    delivery_status = models.CharField(max_length=50, choices=DeliveryStatus.choices, default=DeliveryStatus.CREATED)
    warehouse_stage = models.CharField(max_length=50, choices=WarehouseStage.choices, default=WarehouseStage.INTAKE)
    
    calculated_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    external_expenses_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    description = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    
    is_fragile = models.BooleanField(default=False)
    has_battery = models.BooleanField(default=False)
    is_repacked = models.BooleanField(default=False)
    is_dangerous = models.BooleanField(default=False)
    requires_manual_review = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_items', on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='updated_items', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = _('Груз')
        verbose_name_plural = _('Грузы')

    def __str__(self):
        return self.item_code



class ItemPhoto(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='photos')
    file = models.ImageField(upload_to='items/photos/')
    file_url = models.URLField(max_length=500, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(default=0)
    mime_type = models.CharField(max_length=50, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Фото груза')
        verbose_name_plural = _('Фото грузов')

    def __str__(self):
        return f"Photo for {self.item.item_code}"

class Attachment(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='attachments', null=True, blank=True)
    shipment_group = models.ForeignKey(ShipmentGroup, on_delete=models.CASCADE, related_name='attachments', null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='attachments', null=True, blank=True)
    file_type = models.CharField(max_length=50, choices=AttachmentType.choices, default=AttachmentType.OTHER)
    file = models.FileField(upload_to='attachments/')
    file_url = models.URLField(max_length=500, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(default=0)
    mime_type = models.CharField(max_length=50, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Вложение')
        verbose_name_plural = _('Вложения')

    def __str__(self):
        return f"Attachment {self.file_name}"

class ItemExpense(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='expenses')
    expense_type = models.CharField(max_length=50, choices=ExpenseType.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    comment = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Доп. расход')
        verbose_name_plural = _('Доп. расходы')

    def __str__(self):
        return f"Expense {self.amount} {self.currency} for {self.item.item_code}"

class ItemStatusHistory(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=50, blank=True)
    new_status = models.CharField(max_length=50)
    comment = models.TextField(blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('История статуса груза')
        verbose_name_plural = _('Истории статусов грузов')

    def __str__(self):
        return f"{self.item.item_code} changed to {self.new_status}"
