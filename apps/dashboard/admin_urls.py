"""
URL patterns for admin dashboard JSON API.
Mounted at /admin/dashboard/ in config/urls.py (BEFORE admin.site.urls).
"""
from django.urls import path

from .admin_views import (
    SummaryView,
    ItemsStatusView,
    PaymentsStatusView,
    RevenueExpensesView,
    ItemsByDayView,
    ItemsByDestinationView,
    ItemsByWarehouseView,
    RecentActivityView,
    RecentItemsView,
    RecentPaymentsView,
)

urlpatterns = [
    path('api/summary/',             SummaryView.as_view(),            name='dash-api-summary'),
    path('api/items-status/',        ItemsStatusView.as_view(),        name='dash-api-items-status'),
    path('api/payments-status/',     PaymentsStatusView.as_view(),     name='dash-api-payments-status'),
    path('api/revenue-expenses/',    RevenueExpensesView.as_view(),    name='dash-api-revenue-expenses'),
    path('api/items-by-day/',        ItemsByDayView.as_view(),         name='dash-api-items-by-day'),
    path('api/items-by-destination/',ItemsByDestinationView.as_view(), name='dash-api-items-by-destination'),
    path('api/items-by-warehouse/',  ItemsByWarehouseView.as_view(),   name='dash-api-items-by-warehouse'),
    path('api/recent-activity/',     RecentActivityView.as_view(),     name='dash-api-recent-activity'),
    path('api/recent-items/',        RecentItemsView.as_view(),        name='dash-api-recent-items'),
    path('api/recent-payments/',     RecentPaymentsView.as_view(),     name='dash-api-recent-payments'),
]
