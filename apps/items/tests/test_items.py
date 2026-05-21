import pytest
from rest_framework import status
from django.urls import reverse
from decimal import Decimal
from apps.common.factories import ItemFactory, PriceRuleFactory, ItemExpenseFactory
from apps.common.choices import CalculationType, VolumeSource, DeliveryStatus
from apps.items.models import ItemStatusHistory

pytestmark = pytest.mark.django_db

def test_volume_calculation():
    """Flow 6: Volume calculation from dimensions"""
    item = ItemFactory(
        length_cm=100, width_cm=50, height_cm=50,
        volume_source=VolumeSource.CALCULATED
    )
    item.refresh_from_db()
    # 100 * 50 * 50 = 250,000 cm3 = 0.25 m3
    assert item.volume_m3 == Decimal('0.2500')

def test_price_calculation_by_weight():
    """Flow 7: Price calculation by weight"""
    rule = PriceRuleFactory(calculation_type=CalculationType.WEIGHT, price_per_kg=5.00)
    item = ItemFactory(weight_kg=10, price_rule=rule)
    assert item.calculated_price == Decimal('50.00')

def test_price_calculation_by_volume():
    """Flow 8: Price calculation by volume"""
    rule = PriceRuleFactory(calculation_type=CalculationType.VOLUME, price_per_m3=100.00)
    item = ItemFactory(
        length_cm=100, width_cm=100, height_cm=100,
        volume_source=VolumeSource.CALCULATED,
        price_rule=rule
    )
    # 1 m3 * 100
    assert item.calculated_price == Decimal('100.00')

def test_min_charge_rule():
    """Flow 9: Min charge rule"""
    rule = PriceRuleFactory(calculation_type=CalculationType.WEIGHT, price_per_kg=5.00, min_charge=20.00)
    # 2 kg * 5 = 10 < 20 (min_charge)
    item = ItemFactory(weight_kg=2, price_rule=rule)
    assert item.calculated_price == Decimal('20.00')

def test_item_expense_sync():
    """Flow 10: ItemExpense sync with item.external_expenses_total and item.total_price"""
    rule = PriceRuleFactory(calculation_type=CalculationType.WEIGHT, price_per_kg=5.00)
    item = ItemFactory(weight_kg=10, price_rule=rule)
    
    assert item.calculated_price == Decimal('50.00')
    assert item.external_expenses_total == Decimal('0.00')
    assert item.total_price == Decimal('50.00')
    
    # Add expense
    expense = ItemExpenseFactory(item=item, amount=15.00)
    item.refresh_from_db()
    assert item.external_expenses_total == Decimal('15.00')
    assert item.total_price == Decimal('65.00')
    
    # Delete expense
    expense.delete()
    item.refresh_from_db()
    assert item.external_expenses_total == Decimal('0.00')
    assert item.total_price == Decimal('50.00')

def test_item_delivery_status_transition(superadmin_client):
    """Flow 17 & 19: Delivery status transition validation & History"""
    item = ItemFactory(delivery_status=DeliveryStatus.CREATED)
    url = reverse('items-change-status', args=[item.id])
    
    # Valid transition: CREATED -> AT_CHINA_WAREHOUSE
    response = superadmin_client.post(url, {'delivery_status': DeliveryStatus.AT_CHINA_WAREHOUSE, 'comment': 'Arrived'})
    assert response.status_code == status.HTTP_200_OK
    item.refresh_from_db()
    assert item.delivery_status == DeliveryStatus.AT_CHINA_WAREHOUSE
    
    # History checked
    history = ItemStatusHistory.objects.filter(item=item).last()
    assert history.old_status == DeliveryStatus.CREATED
    assert history.new_status == DeliveryStatus.AT_CHINA_WAREHOUSE
    
    # Invalid transition: AT_CHINA_WAREHOUSE -> DELIVERED
    response = superadmin_client.post(url, {'delivery_status': DeliveryStatus.DELIVERED})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_search_filter_endpoints(superadmin_client):
    """Flow 23: Search/filter endpoints"""
    ItemFactory(item_code='ITM0001', delivery_status=DeliveryStatus.CREATED)
    ItemFactory(item_code='ITM0002', delivery_status=DeliveryStatus.DELIVERED)
    
    url = reverse('items-list')
    # Filter by status
    response = superadmin_client.get(url, {'delivery_status': DeliveryStatus.DELIVERED})
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['item_code'] == 'ITM0002'

def test_file_upload_validation(superadmin_client):
    """Flow 24: File upload validation"""
    from django.core.files.uploadedfile import SimpleUploadedFile
    item = ItemFactory()
    url = reverse('photos-list')
    
    gif_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'
    file = SimpleUploadedFile("test.gif", gif_content, content_type="image/gif")
    response = superadmin_client.post(url, {
        'item': item.id,
        'file': file,
        'file_name': file.name
    }, format='multipart')
    
    if response.status_code != status.HTTP_201_CREATED:
        print(f"FAILED UPLOAD: {response.data}")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert item.photos.count() == 1
