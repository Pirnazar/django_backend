from django.db.models import Sum, Count

def recalculate_shipment_group_totals(shipment_group):
    if not shipment_group:
        return
        
    totals = shipment_group.items.aggregate(
        item_count=Count('id'),
        weight_sum=Sum('weight_kg'),
        volume_sum=Sum('volume_m3')
    )
    
    shipment_group.total_items = totals['item_count'] or 0
    shipment_group.total_weight_kg = totals['weight_sum'] or 0.00
    shipment_group.total_volume_m3 = totals['volume_sum'] or 0.0000
    
    shipment_group.save(update_fields=['total_items', 'total_weight_kg', 'total_volume_m3'])
