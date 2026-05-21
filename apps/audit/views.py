from rest_framework import viewsets
from .models import AuditLog
from .serializers import AuditLogSerializer
from apps.accounts.permissions import IsSuperAdmin

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsSuperAdmin]
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    filterset_fields = ['entity_type', 'action', 'actor']
    search_fields = ['entity_id', 'actor']
