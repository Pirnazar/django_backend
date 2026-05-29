from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Item, ItemPhoto, Attachment, ItemExpense, ItemStatusHistory
from .serializers import (
    ItemSerializer, ItemPhotoSerializer, AttachmentSerializer,
    ItemExpenseSerializer, ItemStatusHistorySerializer,
)
from apps.common.services import generate_item_code
from apps.common.exceptions import TransitionNotAllowed
from apps.accounts.permissions import IsClientOrStaff

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsClientOrStaff]
    search_fields = ['item_code', 'barcode', 'express_code', 'client__client_code', 'client__phone_number']
    filterset_fields = ['client', 'destination', 'warehouse', 'shipment_group', 'payment_status', 'delivery_status', 'warehouse_stage']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False):
            return Item.objects.none()
            
        if user.role == 'client':
            if hasattr(user, 'client_profile'):
                return self.queryset.filter(client=user.client_profile)
            return self.queryset.none()
            
        return self.queryset

    def perform_create(self, serializer):
        item_code = generate_item_code()
        serializer.save(
            item_code=item_code,
            created_by=self.request.user,
            updated_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        item = self.get_object()
        new_status = request.data.get('delivery_status')
        comment = request.data.get('comment', '')
        
        if not new_status:
            return Response({'error': 'delivery_status is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        old_status = item.delivery_status
        if old_status == new_status:
            return Response({'status': 'no change'})
            
        from apps.common.choices import DeliveryStatus
        
        # Simplified State Machine Validation
        allowed_transitions = {
            DeliveryStatus.CREATED: [DeliveryStatus.AT_CHINA_WAREHOUSE, DeliveryStatus.CANCELLED],
            DeliveryStatus.AT_CHINA_WAREHOUSE: [DeliveryStatus.MEASURED],
            DeliveryStatus.MEASURED: [DeliveryStatus.PHOTOGRAPHED, DeliveryStatus.LABELED],
            DeliveryStatus.PHOTOGRAPHED: [DeliveryStatus.LABELED],
            DeliveryStatus.LABELED: [DeliveryStatus.PACKED],
            DeliveryStatus.PACKED: [DeliveryStatus.GROUPED],
            DeliveryStatus.GROUPED: [DeliveryStatus.SENT_TO_URUMQI],
            DeliveryStatus.SENT_TO_URUMQI: [DeliveryStatus.ARRIVED_URUMQI],
            DeliveryStatus.ARRIVED_URUMQI: [DeliveryStatus.SENT_TO_TURKMENISTAN, DeliveryStatus.OUT_FOR_DELIVERY],
            DeliveryStatus.SENT_TO_TURKMENISTAN: [DeliveryStatus.ARRIVED_TURKMENISTAN],
            DeliveryStatus.ARRIVED_TURKMENISTAN: [DeliveryStatus.OUT_FOR_DELIVERY],
            DeliveryStatus.OUT_FOR_DELIVERY: [DeliveryStatus.DELIVERED],
            DeliveryStatus.DELIVERED: [],
            DeliveryStatus.CANCELLED: []
        }
        
        if new_status not in allowed_transitions.get(old_status, []):
            raise TransitionNotAllowed(f"Cannot transition from {old_status} to {new_status}")
            
        item.delivery_status = new_status
        item.save(update_fields=['delivery_status'])
        
        ItemStatusHistory.objects.create(
            item=item,
            old_status=old_status,
            new_status=new_status,
            comment=comment,
            changed_by=request.user
        )
        
        return Response({'status': 'success', 'new_status': new_status})

class ItemExpenseViewSet(viewsets.ModelViewSet):
    queryset = ItemExpense.objects.all()
    serializer_class = ItemExpenseSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ItemPhotoViewSet(viewsets.ModelViewSet):
    queryset = ItemPhoto.objects.all()
    serializer_class = ItemPhotoSerializer

    def perform_create(self, serializer):
        import mimetypes
        file_obj = self.request.data.get('file')
        if file_obj:
            size = file_obj.size
            mime_type = mimetypes.guess_type(file_obj.name)[0] or 'application/octet-stream'
            serializer.save(
                uploaded_by=self.request.user, 
                file_size=size, 
                mime_type=mime_type,
                file_name=file_obj.name
            )
        else:
            serializer.save(uploaded_by=self.request.user)

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
