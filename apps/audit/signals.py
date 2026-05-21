import json
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from .models import AuditLog
from apps.items.models import Item
from apps.shipments.models import ShipmentGroup

# Store old data on the instance before save
@receiver(pre_save, sender=Item)
@receiver(pre_save, sender=ShipmentGroup)
def store_old_data(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_data = model_to_dict(old_instance)
        except sender.DoesNotExist:
            instance._old_data = None
    else:
        instance._old_data = None

@receiver(post_save, sender=Item)
@receiver(post_save, sender=ShipmentGroup)
def audit_log_save(sender, instance, created, **kwargs):
    action = 'CREATE' if created else 'UPDATE'
    new_data = model_to_dict(instance)
    old_data = getattr(instance, '_old_data', None)
    
    # We don't have access to the request object directly in signals
    # In a real app, use threading.local() or django-cuser to get the actor
    actor = 'System' 
    if hasattr(instance, 'updated_by') and instance.updated_by:
        actor = instance.updated_by.email
    elif hasattr(instance, 'created_by') and instance.created_by:
        actor = instance.created_by.email

    try:
        AuditLog.objects.create(
            actor=actor,
            action=action,
            entity_type=sender.__name__,
            entity_id=str(instance.pk),
            old_data=json.loads(json.dumps(old_data, cls=DjangoJSONEncoder)) if old_data else None,
            new_data=json.loads(json.dumps(new_data, cls=DjangoJSONEncoder))
        )
    except Exception:
        pass

@receiver(post_delete, sender=Item)
@receiver(post_delete, sender=ShipmentGroup)
def audit_log_delete(sender, instance, **kwargs):
    old_data = model_to_dict(instance)
    actor = 'System'
    
    try:
        AuditLog.objects.create(
            actor=actor,
            action='DELETE',
            entity_type=sender.__name__,
            entity_id=str(instance.pk),
            old_data=json.loads(json.dumps(old_data, cls=DjangoJSONEncoder))
        )
    except Exception:
        pass
