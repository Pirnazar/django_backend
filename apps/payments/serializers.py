from rest_framework import serializers
from .models import PaymentTransaction

class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = '__all__'
