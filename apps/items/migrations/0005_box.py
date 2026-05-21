# Manually written migration for Box model and Item.box FK.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("items", "0004_item_main_photo"),
        ("locations", "0001_initial"),
        ("shipments", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Box",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("box_code", models.CharField(db_index=True, max_length=50, unique=True)),
                ("barcode", models.CharField(blank=True, db_index=True, max_length=100)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Открыта"),
                            ("closed", "Закрыта"),
                            ("labeled", "Этикетка напечатана"),
                        ],
                        default="open",
                        max_length=20,
                    ),
                ),
                ("total_items", models.IntegerField(default=0)),
                ("total_weight_kg", models.DecimalField(decimal_places=2, default=0.00, max_digits=10)),
                ("total_volume_m3", models.DecimalField(decimal_places=4, default=0.0000, max_digits=10)),
                ("comment", models.TextField(blank=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("printed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "destination",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="boxes",
                        to="locations.destination",
                    ),
                ),
                (
                    "warehouse",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="boxes",
                        to="locations.warehouse",
                    ),
                ),
                (
                    "shipment_group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="boxes",
                        to="shipments.shipmentgroup",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_boxes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "closed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="closed_boxes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Коробка",
                "verbose_name_plural": "Коробки",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="item",
            name="box",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="items",
                to="items.box",
            ),
        ),
    ]
