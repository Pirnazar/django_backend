"""
Dashboard admin API tests.

Coverage:
- All 7+ endpoints return 200 for staff
- Finance data hidden for warehouse/operator
- Finance data visible for manager/admin/superadmin
- Redis cache failure falls back to DB
- Recent tables return at most 5 rows
- Response structure is stable (required keys present)
- Unauthenticated → 401
"""
import json
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client as TestClient
from django.urls import reverse

from apps.accounts.models import StaffUser
from apps.clients.models import Client
from apps.items.models import Item
from apps.locations.models import Destination, Warehouse
from apps.payments.models import PaymentTransaction
from apps.common.choices import (
    StaffRole, DeliveryStatus, PaymentStatus,
    PaymentTransactionStatus, PaymentTransactionType, PaymentMethod,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_user(email, role, **kw):
    return StaffUser.objects.create_user(
        email=email,
        password='testpass123',
        full_name='Test User',
        role=role,
        is_staff=True,
        **kw,
    )


def make_destination():
    return Destination.objects.get_or_create(
        code='TM', defaults={'name': 'Туркменистан', 'is_active': True}
    )[0]


def make_warehouse():
    return Warehouse.objects.get_or_create(
        code='WH1', defaults={'name': 'Склад 1', 'country': 'China', 'city': 'Guangzhou', 'is_active': True}
    )[0]


def make_client(n=1):
    return Client.objects.create(
        client_code=f'C{n:04d}',
        full_name=f'Client {n}',
        phone_number=f'+99361{n:06d}',
        is_active=True,
    )


def make_item(client, dest, wh, n=1):
    return Item.objects.create(
        item_code=f'IT{n:06d}',
        client=client,
        destination=dest,
        warehouse=wh,
        weight_kg=Decimal('1.00'),
        delivery_status=DeliveryStatus.AT_CHINA_WAREHOUSE,
        payment_status=PaymentStatus.UNPAID,
    )


# ── Base test case ────────────────────────────────────────────────────────────

class DashboardBaseTest(TestCase):
    def setUp(self):
        self.manager   = make_user('manager@t.com',   StaffRole.MANAGER)
        self.warehouse = make_user('warehouse@t.com', StaffRole.WAREHOUSE)
        self.operator  = make_user('operator@t.com',  StaffRole.OPERATOR)
        self.admin     = make_user('admin@t.com',     StaffRole.ADMIN)
        self.tc = TestClient()

        # Seed minimal data
        self.dest = make_destination()
        self.wh   = make_warehouse()
        self.client_obj = make_client(1)
        for i in range(1, 7):     # 6 items
            make_item(self.client_obj, self.dest, self.wh, i)

    def get(self, url, user=None):
        user = user or self.manager
        self.tc.force_login(user)
        return self.tc.get(url)


# ── Auth tests ────────────────────────────────────────────────────────────────

class AuthTests(DashboardBaseTest):
    def test_unauthenticated_returns_401(self):
        self.tc.logout()
        res = self.tc.get('/admin/dashboard/api/summary/')
        self.assertEqual(res.status_code, 401)

    def test_non_staff_returns_403(self):
        non_staff = StaffUser.objects.create_user(
            email='ns@t.com', password='pw', full_name='NS',
            role=StaffRole.OPERATOR, is_staff=False,
        )
        self.tc.force_login(non_staff)
        res = self.tc.get('/admin/dashboard/api/summary/')
        self.assertEqual(res.status_code, 403)


# ── Summary endpoint ──────────────────────────────────────────────────────────

class SummaryEndpointTests(DashboardBaseTest):
    URL = '/admin/dashboard/api/summary/'

    def test_manager_gets_200(self):
        res = self.get(self.URL, self.manager)
        self.assertEqual(res.status_code, 200)

    def test_response_has_required_keys(self):
        res = self.get(self.URL, self.manager)
        data = res.json()
        for key in ('total_clients', 'total_items', 'items_china', 'items_unpaid', 'transit_groups'):
            self.assertIn(key, data, f"Missing key: {key}")

    def test_finance_data_visible_for_manager(self):
        res = self.get(self.URL, self.manager)
        data = res.json()
        self.assertIn('monthly_income', data)
        self.assertIn('monthly_expenses', data)
        self.assertTrue(data.get('has_finance'))

    def test_finance_data_hidden_for_warehouse(self):
        res = self.get(self.URL, self.warehouse)
        data = res.json()
        self.assertNotIn('monthly_income', data)
        self.assertNotIn('monthly_expenses', data)
        self.assertFalse(data.get('has_finance'))

    def test_finance_data_hidden_for_operator(self):
        res = self.get(self.URL, self.operator)
        data = res.json()
        self.assertFalse(data.get('has_finance'))

    def test_admin_sees_finance(self):
        res = self.get(self.URL, self.admin)
        data = res.json()
        self.assertTrue(data.get('has_finance'))

    def test_operational_metrics_for_warehouse(self):
        res = self.get(self.URL, self.warehouse)
        data = res.json()
        self.assertIn('items_today', data)
        self.assertIn('awaiting_photo', data)
        self.assertIn('awaiting_pack', data)


# ── Items status ──────────────────────────────────────────────────────────────

class ItemsStatusTests(DashboardBaseTest):
    URL = '/admin/dashboard/api/items-status/'

    def test_returns_200(self):
        res = self.get(self.URL)
        self.assertEqual(res.status_code, 200)

    def test_response_has_items_key(self):
        res = self.get(self.URL)
        data = res.json()
        self.assertIn('items', data)
        self.assertIsInstance(data['items'], list)

    def test_each_row_has_status_and_count(self):
        res = self.get(self.URL)
        for row in res.json()['items']:
            self.assertIn('status', row)
            self.assertIn('count', row)


# ── Payments status ───────────────────────────────────────────────────────────

class PaymentsStatusTests(DashboardBaseTest):
    URL = '/admin/dashboard/api/payments-status/'

    def test_returns_200(self):
        res = self.get(self.URL)
        self.assertEqual(res.status_code, 200)

    def test_response_has_payments_key(self):
        data = self.get(self.URL).json()
        self.assertIn('payments', data)


# ── Revenue endpoint ──────────────────────────────────────────────────────────

class RevenueExpensesTests(DashboardBaseTest):
    URL = '/admin/dashboard/api/revenue-expenses/'

    def test_forbidden_for_warehouse(self):
        res = self.get(self.URL, self.warehouse)
        self.assertEqual(res.status_code, 403)

    def test_forbidden_for_operator(self):
        res = self.get(self.URL, self.operator)
        self.assertEqual(res.status_code, 403)

    def test_allowed_for_manager(self):
        res = self.get(self.URL, self.manager)
        self.assertEqual(res.status_code, 200)

    def test_response_has_chart_keys(self):
        data = self.get(self.URL, self.manager).json()
        self.assertIn('labels', data)
        self.assertIn('revenue', data)
        self.assertIn('expenses', data)
        self.assertEqual(len(data['labels']), len(data['revenue']))


# ── Items by day ──────────────────────────────────────────────────────────────

class ItemsByDayTests(DashboardBaseTest):
    URL = '/admin/dashboard/api/items-by-day/'

    def test_returns_200(self):
        self.assertEqual(self.get(self.URL).status_code, 200)

    def test_30_days_of_labels(self):
        data = self.get(self.URL).json()
        self.assertIn('labels', data)
        self.assertIn('counts', data)
        self.assertEqual(len(data['labels']), 30)
        self.assertEqual(len(data['counts']), 30)


# ── Recent tables — max 5 rows ────────────────────────────────────────────────

class RecentItemsTests(DashboardBaseTest):
    URL = '/admin/dashboard/api/recent-items/'

    def test_returns_at_most_5(self):
        # We already created 6 items in setUp
        data = self.get(self.URL).json()
        self.assertLessEqual(len(data['items']), 5)

    def test_each_row_has_required_fields(self):
        data = self.get(self.URL).json()
        for row in data['items']:
            for field in ('item_code', 'client_name', 'delivery_status', 'created_at', 'admin_url'):
                self.assertIn(field, row)


class RecentPaymentsTests(DashboardBaseTest):
    URL = '/admin/dashboard/api/recent-payments/'

    def setUp(self):
        super().setUp()
        for i in range(1, 7):     # 6 payments
            PaymentTransaction.objects.create(
                client=self.client_obj,
                amount=Decimal('100.00'),
                currency='USD',
                method=PaymentMethod.CASH,
                status=PaymentTransactionStatus.COMPLETED,
                transaction_type=PaymentTransactionType.PAYMENT,
            )

    def test_returns_at_most_5(self):
        data = self.get(self.URL).json()
        self.assertLessEqual(len(data['payments']), 5)

    def test_each_row_has_required_fields(self):
        data = self.get(self.URL).json()
        for row in data['payments']:
            for field in ('id', 'client_name', 'amount', 'currency', 'status', 'created_at'):
                self.assertIn(field, row)


class RecentActivityTests(DashboardBaseTest):
    URL = '/admin/dashboard/api/recent-activity/'

    def test_returns_200(self):
        self.assertEqual(self.get(self.URL).status_code, 200)

    def test_returns_at_most_5(self):
        data = self.get(self.URL).json()
        self.assertLessEqual(len(data['activity']), 5)


# ── Redis cache fallback ──────────────────────────────────────────────────────

class CacheFallbackTests(DashboardBaseTest):
    """Verify that when Redis cache.get raises, the endpoint still works via DB."""

    def _simulate_redis_down(self):
        return patch('apps.dashboard.selectors.cache.get', side_effect=Exception('Redis unavailable'))

    def test_summary_works_without_cache(self):
        with self._simulate_redis_down():
            res = self.get('/admin/dashboard/api/summary/', self.manager)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('total_items', data)

    def test_items_status_works_without_cache(self):
        with self._simulate_redis_down():
            res = self.get('/admin/dashboard/api/items-status/', self.manager)
        self.assertEqual(res.status_code, 200)

    def test_recent_items_works_without_cache(self):
        with self._simulate_redis_down():
            res = self.get('/admin/dashboard/api/recent-items/', self.manager)
        self.assertEqual(res.status_code, 200)


# ── Destination / Warehouse charts ────────────────────────────────────────────

class DestinationWarehouseTests(DashboardBaseTest):
    def test_by_destination_returns_200(self):
        res = self.get('/admin/dashboard/api/items-by-destination/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('destinations', data)

    def test_by_warehouse_returns_200(self):
        res = self.get('/admin/dashboard/api/items-by-warehouse/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('warehouses', data)

    def test_destination_row_has_code_and_count(self):
        data = self.get('/admin/dashboard/api/items-by-destination/').json()
        for row in data['destinations']:
            self.assertIn('code', row)
            self.assertIn('count', row)
