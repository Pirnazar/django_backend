"""
Unfold DASHBOARD_CALLBACK.
Provides initial server-side context for the admin/index.html template.
Charts are rendered client-side (Chart.js); this callback populates the
initial card values and recent tables so the page is useful before JS loads.
"""
import logging

from apps.common.choices import StaffRole
from . import selectors

logger = logging.getLogger(__name__)

FINANCE_ROLES = {StaffRole.SUPERADMIN, StaffRole.ADMIN, StaffRole.MANAGER}


def dashboard_callback(request, context):
    try:
        has_finance = getattr(request.user, 'role', None) in FINANCE_ROLES
        summary = selectors.get_summary()

        context.update({
            'has_finance':    has_finance,
            'cards':          summary,
            'recent_items':   selectors.get_recent_items(),
            'recent_payments': selectors.get_recent_payments(),
            'recent_logs':    selectors.get_recent_activity(),
        })

        if not has_finance:
            context['operational'] = selectors.get_operational()

    except Exception:
        logger.exception("Dashboard callback error")
        context.setdefault('has_finance', False)
        context.setdefault('cards', {})
        context.setdefault('recent_items', [])
        context.setdefault('recent_payments', [])
        context.setdefault('recent_logs', [])

    return context
