import pytest
from decimal import Decimal
from apps.common.factories import ItemFactory, PaymentTransactionFactory, PriceRuleFactory
from apps.common.choices import PaymentTransactionStatus, PaymentTransactionType, CalculationType

pytestmark = pytest.mark.django_db

def test_payment_sync_partial():
    """Flow 11 & 12: PaymentTransaction sync & Partial payment"""
    rule = PriceRuleFactory(calculation_type=CalculationType.WEIGHT, price_per_kg=10.00)
    item = ItemFactory(weight_kg=10, price_rule=rule)
    assert item.total_price == Decimal('100.00')
    assert item.payment_status == 'unpaid'
    
    # Add partial payment
    PaymentTransactionFactory(
        item=item, 
        amount=50.00, 
        status=PaymentTransactionStatus.COMPLETED,
        transaction_type=PaymentTransactionType.PAYMENT
    )
    
    item.refresh_from_db()
    assert item.payment_status == 'partially_paid'

def test_payment_sync_full():
    """Flow 13: Full payment"""
    rule = PriceRuleFactory(calculation_type=CalculationType.WEIGHT, price_per_kg=10.00)
    item = ItemFactory(weight_kg=10, price_rule=rule)
    
    # Add full payment
    PaymentTransactionFactory(
        item=item, 
        amount=100.00, 
        status=PaymentTransactionStatus.COMPLETED,
        transaction_type=PaymentTransactionType.PAYMENT
    )
    
    item.refresh_from_db()
    assert item.payment_status == 'paid'

def test_payment_sync_refund():
    """Flow 14: Refund"""
    rule = PriceRuleFactory(calculation_type=CalculationType.WEIGHT, price_per_kg=10.00)
    item = ItemFactory(weight_kg=10, price_rule=rule)
    
    # Add full payment
    payment = PaymentTransactionFactory(
        item=item, 
        amount=100.00, 
        status=PaymentTransactionStatus.COMPLETED,
        transaction_type=PaymentTransactionType.PAYMENT
    )
    item.refresh_from_db()
    assert item.payment_status == 'paid'
    
    # Add refund
    PaymentTransactionFactory(
        item=item, 
        amount=50.00, 
        status=PaymentTransactionStatus.COMPLETED,
        transaction_type=PaymentTransactionType.REFUND
    )
    item.refresh_from_db()
    assert item.payment_status == 'partially_paid'
    
    # Full refund
    PaymentTransactionFactory(
        item=item, 
        amount=50.00, 
        status=PaymentTransactionStatus.COMPLETED,
        transaction_type=PaymentTransactionType.REFUND
    )
    item.refresh_from_db()
    assert item.payment_status == 'unpaid'
