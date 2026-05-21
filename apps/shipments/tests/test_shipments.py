import pytest
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from apps.common.factories import ItemFactory, ShipmentGroupFactory
from apps.common.choices import ShipmentGroupStatus, VolumeSource
from apps.shipments.models import ShipmentGroupStatusHistory

pytestmark = pytest.mark.django_db

def test_shipment_group_totals_add():
    """Flow 15: ShipmentGroup totals recalculation when item is added"""
    group = ShipmentGroupFactory()
    
    assert group.total_items == 0
    
    item1 = ItemFactory(weight_kg=10)
    item2 = ItemFactory(weight_kg=20)
    
    # Assign items to group
    item1.shipment_group = group
    item1.save()
    item2.shipment_group = group
    item2.save()
    
    group.refresh_from_db()
    assert group.total_items == 2
    assert group.total_weight_kg == Decimal('30.00')

def test_shipment_group_totals_remove():
    """Flow 16: ShipmentGroup totals recalculation when item is removed"""
    group = ShipmentGroupFactory()
    item = ItemFactory(weight_kg=15, shipment_group=group)
    
    group.refresh_from_db()
    assert group.total_items == 1
    assert group.total_weight_kg == Decimal('15.00')
    
    # Remove item
    item.shipment_group = None
    item.save()
    
    group.refresh_from_db()
    assert group.total_items == 0
    assert group.total_weight_kg == Decimal('0.00')

def test_shipment_group_status_validation(superadmin_client):
    """Flow 18 & 20: ShipmentGroup status transition & History"""
    group = ShipmentGroupFactory(status=ShipmentGroupStatus.DRAFT)
    url = reverse('shipmentgroups-change-status', args=[group.id])
    
    # Valid transition
    response = superadmin_client.post(url, {'status': ShipmentGroupStatus.FORMING, 'comment': 'Starting'})
    assert response.status_code == status.HTTP_200_OK
    
    group.refresh_from_db()
    assert group.status == ShipmentGroupStatus.FORMING
    
    # History checked
    history = ShipmentGroupStatusHistory.objects.filter(shipment_group=group).last()
    assert history.old_status == ShipmentGroupStatus.DRAFT
    assert history.new_status == ShipmentGroupStatus.FORMING
    
    # Invalid transition
    response = superadmin_client.post(url, {'status': ShipmentGroupStatus.COMPLETED})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
