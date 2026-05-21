from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import Item, ItemExpense, ItemPhoto
from .services import calculate_item_totals

@receiver(pre_save, sender=Item)
def item_pre_save_calculations(sender, instance, **kwargs):
    # This recalculates volume, pricing, and totals right before the item is saved to DB.
    calculate_item_totals(instance)

@receiver(post_save, sender=ItemExpense)
@receiver(post_delete, sender=ItemExpense)
def update_item_totals_on_expense_change(sender, instance, **kwargs):
    if instance.item:
        item = instance.item
        # Recalculate totals which grabs the new expenses sum
        calculate_item_totals(item)
        item.save(update_fields=['external_expenses_total', 'total_price'])

@receiver(pre_save, sender=Item)
def track_item_shipment_group_removal(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Item.objects.get(pk=instance.pk)
            instance._old_shipment_group_id = old_instance.shipment_group_id
            instance._old_box_id = old_instance.box_id
        except Item.DoesNotExist:
            instance._old_shipment_group_id = None
            instance._old_box_id = None
    else:
        instance._old_shipment_group_id = None
        instance._old_box_id = None

@receiver(post_save, sender=Item)
def handle_item_shipment_group_change(sender, instance, created, **kwargs):
    from apps.shipments.services import recalculate_shipment_group_totals
    from apps.shipments.models import ShipmentGroup
    from apps.items.models import Box
    from apps.items.services import recalculate_box_totals

    new_group_id = instance.shipment_group_id
    old_group_id = getattr(instance, '_old_shipment_group_id', None)

    if old_group_id and old_group_id != new_group_id:
        try:
            old_group = ShipmentGroup.objects.get(pk=old_group_id)
            recalculate_shipment_group_totals(old_group)
        except ShipmentGroup.DoesNotExist:
            pass

    if new_group_id:
        try:
            new_group = ShipmentGroup.objects.get(pk=new_group_id)
            recalculate_shipment_group_totals(new_group)
        except ShipmentGroup.DoesNotExist:
            pass

    new_box_id = instance.box_id
    old_box_id = getattr(instance, '_old_box_id', None)

    if old_box_id and old_box_id != new_box_id:
        try:
            recalculate_box_totals(Box.objects.get(pk=old_box_id))
        except Box.DoesNotExist:
            pass
    if new_box_id:
        try:
            recalculate_box_totals(Box.objects.get(pk=new_box_id))
        except Box.DoesNotExist:
            pass

@receiver(post_save, sender=ItemPhoto)
def trigger_collage_generation(sender, instance, created, **kwargs):
    if created and instance.item:
        from apps.items.services import generate_collage_for_item
        generate_collage_for_item(instance.item)
