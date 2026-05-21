from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Item, ItemPhoto, Attachment, ItemExpense, ItemStatusHistory, Box
from .serializers import (
    ItemSerializer, ItemPhotoSerializer, AttachmentSerializer,
    ItemExpenseSerializer, ItemStatusHistorySerializer, BoxSerializer,
)
from apps.common.services import generate_item_code, generate_box_code
from apps.common.exceptions import TransitionNotAllowed

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    search_fields = ['item_code', 'barcode', 'express_code', 'client__client_code', 'client__phone_number']
    filterset_fields = ['client', 'destination', 'warehouse', 'shipment_group', 'payment_status', 'delivery_status', 'warehouse_stage']

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


class BoxViewSet(viewsets.ModelViewSet):
    queryset = Box.objects.prefetch_related('items', 'items__client').select_related(
        'destination', 'warehouse', 'shipment_group'
    )
    serializer_class = BoxSerializer
    filterset_fields = ['status', 'destination', 'warehouse', 'shipment_group']
    search_fields = ['box_code', 'barcode']

    def perform_create(self, serializer):
        box_code = generate_box_code()
        serializer.save(
            box_code=box_code,
            barcode=serializer.validated_data.get('barcode') or box_code,
            created_by=self.request.user,
        )

    @action(detail=True, methods=['post'], url_path='scan')
    def scan(self, request, pk=None):
        from .services import add_item_to_box, BoxScanError
        box = self.get_object()
        barcode = request.data.get('barcode') or request.data.get('code')
        try:
            item = add_item_to_box(box, barcode, user=request.user)
        except BoxScanError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        box.refresh_from_db()
        return Response({
            'success': True,
            'scanned_item': {
                'id': item.pk,
                'item_code': item.item_code,
                'client_code': item.client.client_code if item.client_id else '',
                'weight_kg': float(item.weight_kg),
                'volume_m3': float(item.volume_m3),
            },
            'box': BoxSerializer(box).data,
        })

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request, pk=None):
        from .services import close_box, BoxScanError
        box = self.get_object()
        try:
            close_box(box, user=request.user)
        except BoxScanError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BoxSerializer(box).data)

    @action(detail=True, methods=['post'], url_path='reopen')
    def reopen(self, request, pk=None):
        from apps.common.choices import BoxStatus
        box = self.get_object()
        if box.status == BoxStatus.OPEN:
            return Response({'error': 'Уже открыта.'}, status=status.HTTP_400_BAD_REQUEST)
        box.status = BoxStatus.OPEN
        box.closed_at = None
        box.printed_at = None
        box.closed_by = None
        box.save(update_fields=['status', 'closed_at', 'printed_at', 'closed_by'])
        return Response(BoxSerializer(box).data)

    @action(detail=True, methods=['post'], url_path='remove-item')
    def remove_item(self, request, pk=None):
        from .services import recalculate_box_totals
        box = self.get_object()
        item_id = request.data.get('item_id')
        try:
            item = box.items.get(pk=item_id)
        except Item.DoesNotExist:
            return Response({'error': 'Груз не найден в коробке.'}, status=status.HTTP_400_BAD_REQUEST)
        item.box = None
        item.save(update_fields=['box', 'updated_by'])
        recalculate_box_totals(box)
        box.refresh_from_db()
        return Response(BoxSerializer(box).data)

    @action(detail=True, methods=['post'], url_path='mark-printed')
    def mark_printed(self, request, pk=None):
        from .services import mark_box_printed
        box = self.get_object()
        mark_box_printed(box)
        return Response(BoxSerializer(box).data)
