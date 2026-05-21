from rest_framework import viewsets
from .models import PaymentTransaction
from .serializers import PaymentTransactionSerializer
from apps.common.choices import PaymentTransactionStatus, PaymentTransactionType

class PaymentTransactionViewSet(viewsets.ModelViewSet):
    queryset = PaymentTransaction.objects.all()
    serializer_class = PaymentTransactionSerializer
    search_fields = ['reference_number', 'comment']
    filterset_fields = ['item', 'client', 'method', 'status', 'transaction_type']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
