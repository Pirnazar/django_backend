from rest_framework import viewsets
from .models import PriceRule
from .serializers import PriceRuleSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal

class PriceRuleViewSet(viewsets.ModelViewSet):
    queryset = PriceRule.objects.all().order_by('-priority', '-created_at')
    serializer_class = PriceRuleSerializer
    filterset_fields = ['destination', 'warehouse', 'is_active', 'calculation_type']
    search_fields = ['name']

    @action(detail=True, methods=['post'], url_path='preview-calculation')
    def preview_calculation(self, request, pk=None):
        rule = self.get_object()
        weight_kg = Decimal(request.data.get('weight_kg', 0))
        volume_m3 = Decimal(request.data.get('volume_m3', 0))
        
        calculated_price = Decimal('0.00')
        if rule.calculation_type == 'weight':
            calculated_price = weight_kg * rule.price_per_kg
        elif rule.calculation_type == 'volume':
            calculated_price = volume_m3 * rule.price_per_m3
        elif rule.calculation_type == 'fixed':
            calculated_price = rule.fixed_price
        elif rule.calculation_type == 'mixed':
            calculated_price = max(weight_kg * rule.price_per_kg, volume_m3 * rule.price_per_m3)
            
        final_price = max(calculated_price, rule.min_charge)
        return Response({
            'calculated_price': str(final_price),
            'currency': rule.currency
        })
