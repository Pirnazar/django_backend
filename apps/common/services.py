from django.db import transaction
from .models import SequenceCounter

from django.db.models import F

def _get_next_sequence(name: str) -> int:
    with transaction.atomic():
        counter, created = SequenceCounter.objects.get_or_create(
            name=name, defaults={'value': 0}
        )
        SequenceCounter.objects.filter(pk=counter.pk).update(value=F('value') + 1)
        counter.refresh_from_db()
        return counter.value

def generate_client_code() -> str:
    seq = _get_next_sequence('client_code')
    return f"CL{seq:05d}"

def generate_item_code() -> str:
    seq = _get_next_sequence('item_code')
    return f"ITM{seq:07d}"

def generate_group_code() -> str:
    seq = _get_next_sequence('group_code')
    return f"GRP{seq:06d}"
