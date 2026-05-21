from rest_framework import serializers
from .models import PriceRule

class PriceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceRule
        fields = '__all__'
