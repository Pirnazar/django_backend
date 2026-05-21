"""
Admin-specific dashboard JSON endpoints.
Authentication: Django session (staff_member_required equivalent returning JSON).
Routes live at /admin/dashboard/api/* (see admin_urls.py).
"""
import logging
from functools import wraps

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

from apps.common.choices import StaffRole
from . import selectors

logger = logging.getLogger(__name__)

FINANCE_ROLES = {StaffRole.SUPERADMIN, StaffRole.ADMIN, StaffRole.MANAGER}


# ── Auth decorator ─────────────────────────────────────────────────────────────

def staff_required_json(view_func):
    """
    Like @staff_member_required but returns JSON 401/403 instead of redirect.
    Suitable for fetch() calls from the admin dashboard JS.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Требуется авторизация'}, status=401)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Нет доступа'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def _has_finance(user) -> bool:
    return getattr(user, 'role', None) in FINANCE_ROLES


# ── Views ──────────────────────────────────────────────────────────────────────

@method_decorator(staff_required_json, name='dispatch')
class SummaryView(View):
    """
    GET /admin/dashboard/api/summary/

    Finance roles  → full data incl. monthly_income / monthly_expenses.
    Other roles    → operational metrics replace finance fields.
    """
    def get(self, request):
        try:
            data = dict(selectors.get_summary())
            if _has_finance(request.user):
                data['has_finance'] = True
            else:
                data.pop('monthly_income', None)
                data.pop('monthly_expenses', None)
                data['has_finance'] = False
                data.update(selectors.get_operational())
            return JsonResponse(data)
        except Exception:
            logger.exception("Dashboard summary error")
            return JsonResponse({'error': 'Ошибка сервера'}, status=500)


@method_decorator(staff_required_json, name='dispatch')
class ItemsStatusView(View):
    """GET /admin/dashboard/api/items-status/"""
    def get(self, request):
        try:
            return JsonResponse({'items': selectors.get_items_by_status()})
        except Exception:
            logger.exception("Items status error")
            return JsonResponse({'error': 'Ошибка сервера'}, status=500)


@method_decorator(staff_required_json, name='dispatch')
class PaymentsStatusView(View):
    """GET /admin/dashboard/api/payments-status/"""
    def get(self, request):
        try:
            return JsonResponse({'payments': selectors.get_payments_by_status()})
        except Exception:
            logger.exception("Payments status error")
            return JsonResponse({'error': 'Ошибка сервера'}, status=500)


@method_decorator(staff_required_json, name='dispatch')
class RevenueExpensesView(View):
    """
    GET /admin/dashboard/api/revenue-expenses/
    Finance roles only.
    """
    def get(self, request):
        if not _has_finance(request.user):
            return JsonResponse({'error': 'Нет доступа к финансовым данным'}, status=403)
        try:
            return JsonResponse(selectors.get_revenue_expenses())
        except Exception:
            logger.exception("Revenue/expenses error")
            return JsonResponse({'error': 'Ошибка сервера'}, status=500)


@method_decorator(staff_required_json, name='dispatch')
class ItemsByDayView(View):
    """GET /admin/dashboard/api/items-by-day/"""
    def get(self, request):
        try:
            return JsonResponse(selectors.get_items_by_day())
        except Exception:
            logger.exception("Items by day error")
            return JsonResponse({'error': 'Ошибка сервера'}, status=500)


@method_decorator(staff_required_json, name='dispatch')
class ItemsByDestinationView(View):
    """GET /admin/dashboard/api/items-by-destination/"""
    def get(self, request):
        try:
            return JsonResponse({'destinations': selectors.get_items_by_destination()})
        except Exception:
            logger.exception("Items by destination error")
            return JsonResponse({'error': 'Ошибка сервера'}, status=500)


@method_decorator(staff_required_json, name='dispatch')
class ItemsByWarehouseView(View):
    """GET /admin/dashboard/api/items-by-warehouse/"""
    def get(self, request):
        try:
            return JsonResponse({'warehouses': selectors.get_items_by_warehouse()})
        except Exception:
            logger.exception("Items by warehouse error")
            return JsonResponse({'error': 'Ошибка сервера'}, status=500)


@method_decorator(staff_required_json, name='dispatch')
class RecentActivityView(View):
    """GET /admin/dashboard/api/recent-activity/"""
    def get(self, request):
        try:
            return JsonResponse({'activity': selectors.get_recent_activity()})
        except Exception:
            logger.exception("Recent activity error")
            return JsonResponse({'error': 'Ошибка сервера'}, status=500)


@method_decorator(staff_required_json, name='dispatch')
class RecentItemsView(View):
    """GET /admin/dashboard/api/recent-items/"""
    def get(self, request):
        try:
            return JsonResponse({'items': selectors.get_recent_items()})
        except Exception:
            logger.exception("Recent items error")
            return JsonResponse({'error': 'Ошибка сервера'}, status=500)


@method_decorator(staff_required_json, name='dispatch')
class RecentPaymentsView(View):
    """GET /admin/dashboard/api/recent-payments/"""
    def get(self, request):
        try:
            return JsonResponse({'payments': selectors.get_recent_payments()})
        except Exception:
            logger.exception("Recent payments error")
            return JsonResponse({'error': 'Ошибка сервера'}, status=500)
