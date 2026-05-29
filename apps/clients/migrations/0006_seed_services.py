"""Seed a default catalogue of additional services."""
from django.db import migrations


DEFAULT_SERVICES = [
    ('Усиленная упаковка', 'Дополнительная защита хрупких грузов.', 5.00, 'USD', False),
    ('Фотоотчёт груза', 'Фотографии груза перед отправкой.', 2.00, 'USD', False),
    ('Страхование', 'Страхование груза. Сумму уточните в комментарии.', 0.00, 'USD', True),
    ('Объединение посылок', 'Объединение нескольких посылок в одну.', 3.00, 'USD', False),
    ('Маркировка «Хрупкое»', 'Специальная маркировка хрупкого груза.', 1.00, 'USD', False),
]


def seed(apps, schema_editor):
    AdditionalService = apps.get_model('clients', 'AdditionalService')
    for name, desc, price, currency, requires_comment in DEFAULT_SERVICES:
        AdditionalService.objects.get_or_create(
            name=name,
            defaults={
                'description': desc,
                'price': price,
                'currency': currency,
                'requires_comment': requires_comment,
                'is_active': True,
            },
        )


def unseed(apps, schema_editor):
    AdditionalService = apps.get_model('clients', 'AdditionalService')
    AdditionalService.objects.filter(name__in=[s[0] for s in DEFAULT_SERVICES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0005_additionalservice_client_delivery_city_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
