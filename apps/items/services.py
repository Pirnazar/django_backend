from decimal import Decimal
from django.db.models import Sum
import io
import uuid
from PIL import Image
from django.core.files.base import ContentFile


def calculate_item_totals(item):
    """
    Calculates the volume, total external expenses, and pricing for an Item.
    Note: Does not call item.save() to avoid recursion when used in pre_save signal.
    """
    from apps.common.choices import VolumeSource
    
    # 1. Volume Calculation
    if item.volume_source == VolumeSource.CALCULATED and item.length_cm and item.width_cm and item.height_cm:
        item.volume_m3 = (item.length_cm * item.width_cm * item.height_cm) / Decimal('1000000.0')

    # 2. External Expenses
    if item.pk:
        # Item exists, can query expenses
        total_expenses = item.expenses.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        item.external_expenses_total = total_expenses
    else:
        item.external_expenses_total = Decimal('0.00')

    # 3. Calculated Price based on PriceRule
    item.calculated_price = Decimal('0.00')
    if item.price_rule:
        rule = item.price_rule
        weight = Decimal(str(item.weight_kg))
        volume = Decimal(str(item.volume_m3))
        
        p_kg = Decimal(str(rule.price_per_kg))
        p_m3 = Decimal(str(rule.price_per_m3))
        p_fixed = Decimal(str(rule.fixed_price))
        p_min = Decimal(str(rule.min_charge))

        calculated = Decimal('0.00')
        if rule.calculation_type == 'weight':
            calculated = weight * p_kg
        elif rule.calculation_type == 'volume':
            calculated = volume * p_m3
        elif rule.calculation_type == 'fixed':
            calculated = p_fixed
        elif rule.calculation_type == 'mixed':
            calculated = max(weight * p_kg, volume * p_m3)
            
        item.calculated_price = max(calculated, p_min)
        
    # 4. Total Price
    item.total_price = item.calculated_price + item.external_expenses_total

def generate_collage_for_item(item):
    """
    Generates a collage (side-by-side) of the first two photos of an item.
    Saves it as the main_photo of the item.
    """
    if item.main_photo:
        return # Already has a main photo

    photos = item.photos.all().order_by('created_at')[:2]
    if len(photos) < 2:
        return

    try:
        # Load images
        img1 = Image.open(photos[0].file)
        img2 = Image.open(photos[1].file)
        
        # We want to concatenate them side by side
        # To do this cleanly, let's scale them to the same height
        target_height = 800
        
        # Resize img1
        aspect_ratio_1 = img1.width / img1.height
        new_width_1 = int(target_height * aspect_ratio_1)
        img1 = img1.resize((new_width_1, target_height), Image.Resampling.LANCZOS)
        
        # Resize img2
        aspect_ratio_2 = img2.width / img2.height
        new_width_2 = int(target_height * aspect_ratio_2)
        img2 = img2.resize((new_width_2, target_height), Image.Resampling.LANCZOS)
        
        # Create collage
        collage_width = new_width_1 + new_width_2
        collage = Image.new('RGB', (collage_width, target_height))
        collage.paste(img1, (0, 0))
        collage.paste(img2, (new_width_1, 0))
        
        # Save to buffer
        buffer = io.BytesIO()
        collage.save(buffer, format='JPEG', quality=85)
        
        # Save to item
        filename = f"collage_{item.item_code}_{uuid.uuid4().hex[:8]}.jpg"
        item.main_photo.save(filename, ContentFile(buffer.getvalue()), save=True)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create collage for item {item.item_code}: {e}")
