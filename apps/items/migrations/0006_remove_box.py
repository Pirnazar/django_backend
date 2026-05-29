# Removes the Box model and Item.box FK (Box feature dropped).
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("items", "0005_box"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="item",
            name="box",
        ),
        migrations.DeleteModel(
            name="Box",
        ),
    ]
