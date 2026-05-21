import pytest
from rest_framework.test import APIClient
from apps.common.factories import (
    StaffUserFactory, DestinationFactory, WarehouseFactory,
    ClientFactory, PriceRuleFactory, ShipmentGroupFactory,
    ItemFactory, ItemExpenseFactory, PaymentTransactionFactory
)

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def superadmin_user():
    return StaffUserFactory(role='superadmin', is_superuser=True, is_staff=True)

@pytest.fixture
def operator_user():
    return StaffUserFactory(role='operator')

@pytest.fixture
def superadmin_client(api_client, superadmin_user):
    api_client.force_authenticate(user=superadmin_user)
    return api_client

@pytest.fixture
def operator_client(api_client, operator_user):
    api_client.force_authenticate(user=operator_user)
    return api_client
