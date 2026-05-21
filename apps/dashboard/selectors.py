"""
Dashboard selectors — all ORM queries with Redis cache fallback.
TTLs: summary/recent = 30 s, charts = 60 s.
"""
import logging
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Count, Sum
from django.db.models.functions import TruncDay
from django.utils import timezone
from django.utils.timezone import get_current_timezone

logger = logging.getLogger(__name__)

# ── Status groups ──────────────────────────────────────────────────────────────

CHINA_STATUSES = [
    'created', 'at_china_warehouse', 'measured',
    'photographed', 'labeled', 'packed', 'grouped',
]
TRANSIT_STATUSES = [
    'in_transit_to_urumqi',
    'in_transit_to_turkmenistan',
]


# ── Cache helper ───────────────────────────────────────────────────────────────

def _cached(key: str, ttl: int, fn):
    """
    Try to get `key` from Redis cache.
    On cache.get failure fall back directly to fn().
    On cache.set failure log and return the value anyway.
    """
    try:
        val = cache.get(key)
        if val is not None:
            return val
    except Exception:
        logger.warning("Cache GET error for key '%s', querying DB directly", key)
        return fn()

    val = fn()

    try:
        cache.set(key, val, ttl)
    except Exception:
        logger.warning("Cache SET error for key '%s'", key)

    return val


# ── Date helpers ───────────────────────────────────────────────────────────────

def _month_range():
    now = timezone.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, now


def _today_range():
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


# ── Summary (finance + base) ───────────────────────────────────────────────────

def _fetch_summary() -> dict:
    from apps.clients.models import Client
    from apps.items.models import Item, ItemExpense
    from apps.shipments.models import ShipmentGroup
    from apps.payments.models import PaymentTransaction
    from apps.common.choices import (
        PaymentStatus, PaymentTransactionStatus, PaymentTransactionType,
    )

    month_start, _ = _month_range()

    total_clients  = Client.objects.count()
    active_clients = Client.objects.filter(is_active=True).count()

    total_items   = Item.objects.count()
    items_china   = Item.objects.filter(delivery_status__in=CHINA_STATUSES).count()
    items_unpaid  = Item.objects.filter(payment_status=PaymentStatus.UNPAID).count()
    items_partial = Item.objects.filter(payment_status=PaymentStatus.PARTIALLY_PAID).count()

    transit_groups = ShipmentGroup.objects.filter(status__in=TRANSIT_STATUSES).count()

    income_row = PaymentTransaction.objects.filter(
        status=PaymentTransactionStatus.COMPLETED,
        transaction_type=PaymentTransactionType.PAYMENT,
        created_at__gte=month_start,
    ).aggregate(total=Sum('amount'))
    monthly_income = float(income_row['total'] or 0)

    from apps.items.models import ItemExpense as IE
    expense_row = IE.objects.filter(
        created_at__gte=month_start,
    ).aggregate(total=Sum('amount'))
    monthly_expenses = float(expense_row['total'] or 0)

    return {
        'total_clients':   total_clients,
        'active_clients':  active_clients,
        'total_items':     total_items,
        'items_china':     items_china,
        'items_unpaid':    items_unpaid,
        'items_partial':   items_partial,
        'transit_groups':  transit_groups,
        'monthly_income':  monthly_income,
        'monthly_expenses': monthly_expenses,
    }


def get_summary() -> dict:
    return _cached('dash:summary', 30, _fetch_summary)


# ── Operational metrics (warehouse / operator) ─────────────────────────────────

def _fetch_operational() -> dict:
    from apps.items.models import Item
    from apps.common.choices import WarehouseStage

    today_start, _ = _today_range()

    return {
        'items_today':    Item.objects.filter(created_at__gte=today_start).count(),
        'awaiting_photo': Item.objects.filter(warehouse_stage=WarehouseStage.MEASURED).count(),
        'awaiting_pack':  Item.objects.filter(warehouse_stage=WarehouseStage.PHOTOGRAPHED).count(),
        'awaiting_group': Item.objects.filter(warehouse_stage=WarehouseStage.LABELED).count(),
    }


def get_operational() -> dict:
    return _cached('dash:operational', 30, _fetch_operational)


# ── Items by delivery_status ───────────────────────────────────────────────────

def _fetch_items_by_status() -> list:
    from apps.items.models import Item

    rows = (
        Item.objects
        .values('delivery_status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return [{'status': r['delivery_status'], 'count': r['count']} for r in rows]


def get_items_by_status() -> list:
    return _cached('dash:items_status', 60, _fetch_items_by_status)


# ── Payments by payment_status ─────────────────────────────────────────────────

def _fetch_payments_by_status() -> list:
    from apps.items.models import Item

    rows = (
        Item.objects
        .values('payment_status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return [{'status': r['payment_status'], 'count': r['count']} for r in rows]


def get_payments_by_status() -> list:
    return _cached('dash:payments_status', 60, _fetch_payments_by_status)


# ── Revenue & expenses (daily, current month) ──────────────────────────────────

def _fetch_revenue_expenses() -> dict:
    from apps.payments.models import PaymentTransaction
    from apps.items.models import ItemExpense
    from apps.common.choices import PaymentTransactionStatus, PaymentTransactionType

    month_start, now = _month_range()
    tz = get_current_timezone()

    revenue_qs = (
        PaymentTransaction.objects
        .filter(
            status=PaymentTransactionStatus.COMPLETED,
            transaction_type=PaymentTransactionType.PAYMENT,
            created_at__gte=month_start,
        )
        .annotate(day=TruncDay('created_at', tzinfo=tz))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )

    expense_qs = (
        ItemExpense.objects
        .filter(created_at__gte=month_start)
        .annotate(day=TruncDay('created_at', tzinfo=tz))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )

    revenue_by_day = {r['day'].strftime('%d.%m'): float(r['total']) for r in revenue_qs}
    expense_by_day = {r['day'].strftime('%d.%m'): float(r['total']) for r in expense_qs}

    labels, revenue, expenses = [], [], []
    d = month_start.date()
    end = now.date()
    while d <= end:
        label = d.strftime('%d.%m')
        labels.append(label)
        revenue.append(revenue_by_day.get(label, 0))
        expenses.append(expense_by_day.get(label, 0))
        d += timedelta(days=1)

    return {'labels': labels, 'revenue': revenue, 'expenses': expenses}


def get_revenue_expenses() -> dict:
    return _cached('dash:revenue_expenses', 60, _fetch_revenue_expenses)


# ── New items per day (last 30 days) ───────────────────────────────────────────

def _fetch_items_by_day() -> dict:
    from apps.items.models import Item

    now = timezone.now()
    start = now - timedelta(days=29)
    tz = get_current_timezone()

    qs = (
        Item.objects
        .filter(created_at__gte=start)
        .annotate(day=TruncDay('created_at', tzinfo=tz))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    by_day = {r['day'].strftime('%d.%m'): r['count'] for r in qs}

    labels, counts = [], []
    d = start.date()
    end = now.date()
    while d <= end:
        label = d.strftime('%d.%m')
        labels.append(label)
        counts.append(by_day.get(label, 0))
        d += timedelta(days=1)

    return {'labels': labels, 'counts': counts}


def get_items_by_day() -> dict:
    return _cached('dash:items_by_day', 60, _fetch_items_by_day)


# ── Items by destination (top 10) ─────────────────────────────────────────────

def _fetch_items_by_destination() -> list:
    from apps.items.models import Item

    qs = (
        Item.objects
        .values('destination__code', 'destination__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    return [
        {
            'code':  r['destination__code'] or '—',
            'name':  r['destination__name'] or '—',
            'count': r['count'],
        }
        for r in qs
    ]


def get_items_by_destination() -> list:
    return _cached('dash:items_by_dest', 60, _fetch_items_by_destination)


# ── Items by warehouse ─────────────────────────────────────────────────────────

def _fetch_items_by_warehouse() -> list:
    from apps.items.models import Item

    qs = (
        Item.objects
        .values('warehouse__code', 'warehouse__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return [
        {
            'code':  r['warehouse__code'] or '—',
            'name':  r['warehouse__name'] or '—',
            'count': r['count'],
        }
        for r in qs
    ]


def get_items_by_warehouse() -> list:
    return _cached('dash:items_by_wh', 60, _fetch_items_by_warehouse)


# ── Recent items (5 rows) ──────────────────────────────────────────────────────

def _fetch_recent_items() -> list:
    from apps.items.models import Item

    qs = (
        Item.objects
        .select_related('client', 'destination')
        .order_by('-created_at')[:5]
    )
    return [
        {
            'item_code':              i.item_code,
            'client_code':            i.client.client_code if i.client else '—',
            'client_name':            (i.client.full_name[:20] if i.client else '—'),
            'delivery_status':        i.delivery_status,
            'delivery_status_display': i.get_delivery_status_display(),
            'total_price':            float(i.total_price),
            'currency':               i.declared_value_currency or 'USD',
            'created_at':             i.created_at.strftime('%d.%m.%Y'),
            'admin_url':              f'/admin/items/item/{i.pk}/change/',
        }
        for i in qs
    ]


def get_recent_items() -> list:
    return _cached('dash:recent_items', 30, _fetch_recent_items)


# ── Recent payments (5 rows) ──────────────────────────────────────────────────

def _fetch_recent_payments() -> list:
    from apps.payments.models import PaymentTransaction

    qs = (
        PaymentTransaction.objects
        .select_related('client', 'item')
        .order_by('-created_at')[:5]
    )
    return [
        {
            'id':             p.pk,
            'client_code':    p.client.client_code if p.client else '—',
            'client_name':    (p.client.full_name[:20] if p.client else '—'),
            'item_code':      p.item.item_code if p.item else '—',
            'amount':         float(p.amount),
            'currency':       p.currency,
            'status':         p.status,
            'status_display': p.get_status_display(),
            'created_at':     p.created_at.strftime('%d.%m.%Y'),
            'admin_url':      f'/admin/payments/paymenttransaction/{p.pk}/change/',
        }
        for p in qs
    ]


def get_recent_payments() -> list:
    return _cached('dash:recent_payments', 30, _fetch_recent_payments)


# ── Recent audit activity (5 rows) ────────────────────────────────────────────

def _fetch_recent_activity() -> list:
    from apps.audit.models import AuditLog

    qs = AuditLog.objects.order_by('-created_at')[:5]
    return [
        {
            'action':      l.action,
            'entity_type': l.entity_type,
            'entity_id':   l.entity_id,
            'actor':       l.actor or 'Система',
            'created_at':  l.created_at.strftime('%d.%m.%Y %H:%M'),
        }
        for l in qs
    ]


def get_recent_activity() -> list:
    return _cached('dash:recent_activity', 30, _fetch_recent_activity)
