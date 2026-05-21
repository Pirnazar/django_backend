import pytest
from apps.common.services import generate_client_code, generate_item_code, generate_group_code
from apps.common.models import SequenceCounter
from django.contrib.auth import get_user_model

User = get_user_model()
pytestmark = pytest.mark.django_db

def test_client_code_generation():
    """Flow 3: Client code auto-generation"""
    code1 = generate_client_code()
    code2 = generate_client_code()
    
    assert code1.startswith('CL')
    assert code2.startswith('CL')
    assert code1 != code2
    assert int(code2.replace('CL', '')) == int(code1.replace('CL', '')) + 1

def test_item_code_generation():
    """Flow 4: Item code auto-generation"""
    code = generate_item_code()
    assert code.startswith('ITM')
    assert len(code) == 10  # ITM + 7 digits

def test_group_code_generation():
    """Flow 5: Group code auto-generation"""
    code = generate_group_code()
    assert code.startswith('GRP')
    assert len(code) == 9  # GRP + 6 digits

def test_soft_delete_behavior():
    """Flow 22: Soft delete behavior"""
    user = User.objects.create(email='test@test.com', full_name='Test User')
    assert User.objects.count() == 1
    
    user.delete()
    
    # Should still be in default manager since we removed SoftDeleteManager from StaffUser
    assert User.objects.count() == 1
    # Should be inactive
    user.refresh_from_db()
    assert not user.is_active
    assert user.deleted_at is not None
