from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.common.models import TimeStampedSoftDeleteModel
from apps.locations.models import Destination, Warehouse
from apps.common.choices import ShipmentGroupStatus

class ShipmentGroup(TimeStampedSoftDeleteModel):
    group_code = models.CharField(max_length=50, unique=True, db_index=True)
    destination = models.ForeignKey(Destination, on_delete=models.PROTECT, related_name='shipment_groups')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='shipment_groups')
    total_items = models.IntegerField(default=0)
    total_weight_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_volume_m3 = models.DecimalField(max_digits=10, decimal_places=4, default=0.0000)
    
    china_to_urumqi_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    china_to_turkmenistan_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    sent_to_urumqi_date = models.DateTimeField(null=True, blank=True)
    arrived_urumqi_date = models.DateTimeField(null=True, blank=True)
    sent_to_turkmenistan_date = models.DateTimeField(null=True, blank=True)
    arrived_turkmenistan_date = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=50, choices=ShipmentGroupStatus.choices, default=ShipmentGroupStatus.DRAFT)
    comment = models.TextField(blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_groups', on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='updated_groups', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Партия')
        verbose_name_plural = _('Партии')

    def __str__(self):
        return f"{self.group_code} - {self.status}"

class ShipmentGroupStatusHistory(models.Model):
    shipment_group = models.ForeignKey(ShipmentGroup, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=50, blank=True)
    new_status = models.CharField(max_length=50)
    comment = models.TextField(blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
