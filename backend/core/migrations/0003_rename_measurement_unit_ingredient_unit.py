# Generated by Django 5.1 on 2024-08-23 02:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_rename_unit_ingredient_measurement_unit"),
    ]

    operations = [
        migrations.RenameField(
            model_name="ingredient",
            old_name="measurement_unit",
            new_name="unit",
        ),
    ]
