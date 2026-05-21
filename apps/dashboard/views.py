"""DRF dashboard view — kept for backwards-compat at /api/v1/dashboard/summary/."""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from . import selectors


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(selectors.get_summary())
