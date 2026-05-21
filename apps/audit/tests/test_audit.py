import pytest
import json
from apps.common.factories import ItemFactory
from apps.audit.models import AuditLog

pytestmark = pytest.mark.django_db

def test_audit_log_creation():
    """Flow 21: AuditLog creation for important actions"""
    initial_audit_count = AuditLog.objects.count()
    
    # Create item
    item = ItemFactory(weight_kg=10)
    
    # Audit log should be created
    assert AuditLog.objects.count() == initial_audit_count + 1
    
    log = AuditLog.objects.first()  # ordered by -created_at
    assert log.action == 'CREATE'
    assert log.entity_type == 'Item'
    assert log.entity_id == str(item.pk)
    assert log.old_data is None
    assert log.new_data is not None
    assert float(log.new_data['weight_kg']) == 10.00
    
    # Update item
    item.weight_kg = 15
    item.save()
    
    assert AuditLog.objects.count() == initial_audit_count + 2
    update_log = AuditLog.objects.first()
    assert update_log.action == 'UPDATE'
    assert update_log.entity_type == 'Item'
    assert update_log.old_data is not None
    assert float(update_log.old_data['weight_kg']) == 10.00
    assert float(update_log.new_data['weight_kg']) == 15.00
