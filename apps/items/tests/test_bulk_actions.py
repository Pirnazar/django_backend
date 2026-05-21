"""
Tests for ItemAdmin bulk actions.
"""
import pytest

from apps.common.choices import DeliveryStatus
from apps.common.factories import (
    ItemFactory, ShipmentGroupFactory, DestinationFactory, WarehouseFactory, StaffUserFactory,
)
from apps.items.models import Item, ItemStatusHistory


@pytest.fixture
def superadmin_client(db):
    from django.test import Client as TestClient
    user = StaffUserFactory(is_staff=True, is_superuser=True)
    tc = TestClient()
    tc.force_login(user)
    return tc


@pytest.mark.django_db
def test_add_to_group_assigns_items(superadmin_client):
    group = ShipmentGroupFactory()
    items = [
        ItemFactory(destination=group.destination, warehouse=group.warehouse, shipment_group=None)
        for _ in range(3)
    ]
    superadmin_client.post(
        '/admin/items/item/',
        {
            'action': 'action_add_to_group',
            '_selected_action': [i.pk for i in items],
            'apply': '1',
            'group_id': group.pk,
        },
    )
    for item in items:
        item.refresh_from_db()
        assert item.shipment_group == group


@pytest.mark.django_db
def test_add_to_group_incompatible_destination_blocked(superadmin_client):
    group = ShipmentGroupFactory()
    other_dest = DestinationFactory()
    item = ItemFactory(destination=other_dest, shipment_group=None)

    superadmin_client.post(
        '/admin/items/item/',
        {
            'action': 'action_add_to_group',
            '_selected_action': [item.pk],
            'apply': '1',
            'group_id': group.pk,
        },
    )
    item.refresh_from_db()
    assert item.shipment_group is None


@pytest.mark.django_db
def test_change_status_valid_transition(superadmin_client):
    item = ItemFactory(delivery_status=DeliveryStatus.AT_CHINA_WAREHOUSE)
    superadmin_client.post(
        '/admin/items/item/',
        {
            'action': 'action_change_status',
            '_selected_action': [item.pk],
            'apply': '1',
            'new_status': DeliveryStatus.MEASURED,
            'comment': 'bulk test',
        },
    )
    item.refresh_from_db()
    assert item.delivery_status == DeliveryStatus.MEASURED
    assert ItemStatusHistory.objects.filter(item=item, new_status=DeliveryStatus.MEASURED).exists()


@pytest.mark.django_db
def test_change_status_invalid_transition_blocked(superadmin_client):
    item = ItemFactory(delivery_status=DeliveryStatus.CREATED)
    superadmin_client.post(
        '/admin/items/item/',
        {
            'action': 'action_change_status',
            '_selected_action': [item.pk],
            'apply': '1',
            'new_status': DeliveryStatus.MEASURED,  # CREATED → MEASURED not allowed
            'comment': '',
        },
    )
    item.refresh_from_db()
    assert item.delivery_status == DeliveryStatus.CREATED


@pytest.mark.django_db
def test_excel_export_returns_xlsx(superadmin_client):
    ItemFactory.create_batch(3)
    pks = list(Item.objects.values_list('pk', flat=True))
    res = superadmin_client.post(
        '/admin/items/item/',
        {
            'action': 'action_export_excel',
            '_selected_action': pks,
        },
    )
    assert res.status_code == 200
    assert 'spreadsheetml' in res['Content-Type']
    assert 'attachment' in res.get('Content-Disposition', '')


@pytest.mark.django_db
def test_label_preview_renders_item_codes(superadmin_client):
    items = ItemFactory.create_batch(2)
    res = superadmin_client.post(
        '/admin/items/item/',
        {
            'action': 'action_label_preview',
            '_selected_action': [i.pk for i in items],
        },
    )
    assert res.status_code == 200
    content = res.content.decode()
    for item in items:
        assert item.item_code in content
