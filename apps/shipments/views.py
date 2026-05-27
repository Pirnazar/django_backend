from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ShipmentGroup
from .serializers import ShipmentGroupSerializer
from apps.common.services import generate_group_code
from apps.accounts.permissions import IsClientOrStaff

class ShipmentGroupViewSet(viewsets.ModelViewSet):
    queryset = ShipmentGroup.objects.all()
    serializer_class = ShipmentGroupSerializer
    permission_classes = [IsClientOrStaff]
    search_fields = ['group_code', 'comment']
    filterset_fields = ['destination', 'warehouse', 'status']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return ShipmentGroup.objects.none()
            
        if user.role == 'client':
            if hasattr(user, 'client_profile'):
                return self.queryset.filter(items__client=user.client_profile).distinct()
            return self.queryset.none()
            
        return self.queryset

    def perform_create(self, serializer):
        group_code = generate_group_code()
        serializer.save(
            group_code=group_code,
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        group = self.get_object()
        new_status = request.data.get('status')
        comment = request.data.get('comment', '')
        
        if not new_status:
            return Response({'error': 'status is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        old_status = group.status
        if old_status == new_status:
            return Response({'status': 'no change'})
            
        from apps.common.choices import ShipmentGroupStatus
        from apps.common.exceptions import TransitionNotAllowed
        from apps.shipments.models import ShipmentGroupStatusHistory
        
        allowed_transitions = {
            ShipmentGroupStatus.DRAFT: [ShipmentGroupStatus.FORMING, ShipmentGroupStatus.CANCELLED],
            ShipmentGroupStatus.FORMING: [ShipmentGroupStatus.READY_TO_DISPATCH],
            ShipmentGroupStatus.READY_TO_DISPATCH: [ShipmentGroupStatus.IN_TRANSIT_TO_URUMQI],
            ShipmentGroupStatus.IN_TRANSIT_TO_URUMQI: [ShipmentGroupStatus.ARRIVED_URUMQI],
            ShipmentGroupStatus.ARRIVED_URUMQI: [ShipmentGroupStatus.IN_TRANSIT_TO_TURKMENISTAN, ShipmentGroupStatus.COMPLETED],
            ShipmentGroupStatus.IN_TRANSIT_TO_TURKMENISTAN: [ShipmentGroupStatus.ARRIVED_TURKMENISTAN],
            ShipmentGroupStatus.ARRIVED_TURKMENISTAN: [ShipmentGroupStatus.COMPLETED],
            ShipmentGroupStatus.COMPLETED: [],
            ShipmentGroupStatus.CANCELLED: []
        }
        
        if new_status not in allowed_transitions.get(old_status, []):
            raise TransitionNotAllowed(f"Cannot transition from {old_status} to {new_status}")
            
        group.status = new_status
        group.save(update_fields=['status'])
        
        ShipmentGroupStatusHistory.objects.create(
            shipment_group=group,
            old_status=old_status,
            new_status=new_status,
            comment=comment,
            changed_by=request.user
        )
        
        return Response({'status': 'success', 'new_status': new_status})
