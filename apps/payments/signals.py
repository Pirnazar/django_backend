from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PaymentTransaction
from apps.common.choices import PaymentTransactionStatus, PaymentTransactionType
from django.db.models import Sum

def sync_item_payment_status(item):
    if not item:
        return
        
    completed_payments = item.payments.filter(
        status=PaymentTransactionStatus.COMPLETED,
        transaction_type=PaymentTransactionType.PAYMENT
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    refunds = item.payments.filter(
        status=PaymentTransactionStatus.COMPLETED,
        transaction_type=PaymentTransactionType.REFUND
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    net_paid = completed_payments - refunds
    
    if net_paid <= 0:
        item.payment_status = 'unpaid'
    elif net_paid >= item.total_price:
        item.payment_status = 'paid'
    else:
        item.payment_status = 'partially_paid'
        
    item.save(update_fields=['payment_status'])

@receiver(post_save, sender=PaymentTransaction)
@receiver(post_delete, sender=PaymentTransaction)
def handle_payment_transaction_change(sender, instance, **kwargs):
    if instance.item:
        sync_item_payment_status(instance.item)
