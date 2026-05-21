"""
Tests for Shipment Group Builder views.
"""
import json
import pytest

from apps.common.choices import DeliveryStatus, ShipmentGroupStatus
from apps.common.factories import (
    ItemFactory, ShipmentGroupFactory, DestinationFactory, WarehouseFactory, StaffUserFactory,
)
from apps.items.models import ItemStatusHistory
from apps.shipments.models import ShipmentGroup


@pytest.fixture
def builder_client(db):
    from django.test import Client as TestClient
    user = StaffUserFactory(is_staff=True, is_superuser=True)
    tc = TestClient()
    tc.force_login(user)
    return tc, user


@pytest.mark.django_db
def test_builder_page_returns_200(builder_client):
    tc, _ = builder_client
    res = tc.get('/admin/shipment-group-builder/')
    assert res.status_code == 200


@pytest.mark.django_db
def test_items_api_returns_only_ungrouped(builder_client):
    tc, _ = builder_client
    dest = DestinationFactory()
    wh = WarehouseFactory()
    group = ShipmentGroupFactory(destination=dest, warehouse=wh)

    ungrouped = ItemFactory(destination=dest, warehouse=wh, shipment_group=None)
    ItemFactory(destination=dest, warehouse=wh, shipment_group=group)  # grouped — must be excluded

    res = tc.get(f'/admin/shipment-group-builder/api/items/?destination_id={dest.pk}&warehouse_id={wh.pk}')
    assert res.status_code == 200
    data = res.json()
    ids = [i['id'] for i in data['items']]
    assert ungrouped.pk in ids
    assert all(i['id'] != group.pk for i in data['items'])


@pytest.mark.django_db
def test_items_api_filters_by_dest_wh(builder_client):
    tc, _ = builder_client
    dest1 = DestinationFactory()
    dest2 = DestinationFactory()
    wh = WarehouseFactory()

    item1 = ItemFactory(destination=dest1, warehouse=wh, shipment_group=None)
    ItemFactory(destination=dest2, warehouse=wh, shipment_group=None)

    res = tc.get(f'/admin/shipment-group-builder/api/items/?destination_id={dest1.pk}&warehouse_id={wh.pk}')
    data = res.json()
    ids = [i['id'] for i in data['items']]
    assert item1.pk in ids
    assert len(ids) == 1


@pytest.mark.django_db
def test_create_group_assigns_items(builder_client):
    tc, user = builder_client
    dest = DestinationFactory()
    wh = WarehouseFactory()
    items = [ItemFactory(destination=dest, warehouse=wh, shipment_group=None) for _ in range(3)]

    payload = {
        'destination_id': dest.pk,
        'warehouse_id': wh.pk,
        'item_ids': [i.pk for i in items],
        'group_code': 'TESTGRP001',
        'status': ShipmentGroupStatus.FORMING,
        'comment': '',
    }
    res = tc.post(
        '/admin/shipment-group-builder/api/create/',
        data=json.dumps(payload),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = res.json()
    assert data['success'] is True

    group = ShipmentGroup.objects.get(group_code='TESTGRP001')
    for item in items:
        item.refresh_from_db()
        assert item.shipment_group == group


@pytest.mark.django_db
def test_create_group_recalculates_totals(builder_client):
    tc, _ = builder_client
    dest = DestinationFactory()
    wh = WarehouseFactory()
    from decimal import Decimal
    items = [ItemFactory(destination=dest, warehouse=wh, shipment_group=None, weight_kg=Decimal('2.00')) for _ in range(4)]

    payload = {
        'destination_id': dest.pk,
        'warehouse_id': wh.pk,
        'item_ids': [i.pk for i in items],
        'group_code': 'TESTGRP002',
        'status': ShipmentGroupStatus.FORMING,
        'comment': '',
    }
    tc.post(
        '/admin/shipment-group-builder/api/create/',
        data=json.dumps(payload),
        content_type='application/json',
    )
    group = ShipmentGroup.objects.get(group_code='TESTGRP002')
    assert group.total_items == 4


@pytest.mark.django_db
def test_create_group_transitions_packed_items(builder_client):
    tc, user = builder_client
    dest = DestinationFactory()
    wh = WarehouseFactory()
    packed_item = ItemFactory(destination=dest, warehouse=wh, shipment_group=None, delivery_status=DeliveryStatus.PACKED)

    payload = {
        'destination_id': dest.pk,
        'warehouse_id': wh.pk,
        'item_ids': [packed_item.pk],
        'group_code': 'TESTGRP003',
        'status': ShipmentGroupStatus.FORMING,
        'comment': '',
    }
    tc.post(
        '/admin/shipment-group-builder/api/create/',
        data=json.dumps(payload),
        content_type='application/json',
    )
    packed_item.refresh_from_db()
    assert packed_item.delivery_status == DeliveryStatus.GROUPED
    assert ItemStatusHistory.objects.filter(item=packed_item, new_status=DeliveryStatus.GROUPED).exists()
