import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db

def test_user_authentication(api_client, operator_user):
    """Flow 1: StaffUser authentication"""
    url = reverse('token_obtain_pair')
    response = api_client.post(url, {
        'email': operator_user.email,
        'password': 'password123'
    })
    
    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.data
    assert 'refresh' in response.data

def test_role_based_permissions(api_client, operator_user, superadmin_user):
    """Flow 2: Role-based permissions"""
    audit_url = reverse('audit-list')
    
    # Unauthenticated
    response = api_client.get(audit_url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Operator (Forbidden)
    api_client.force_authenticate(user=operator_user)
    response = api_client.get(audit_url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    
    # Superadmin (Allowed)
    api_client.force_authenticate(user=superadmin_user)
    response = api_client.get(audit_url)
    assert response.status_code == status.HTTP_200_OK
