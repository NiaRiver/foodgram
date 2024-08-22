# Generated by Django 5.1 on 2024-08-21 13:25

import core.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_ingredient_tag_recipe_recipeingredient'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShortenedRecipeURL',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_code', models.CharField(default=core.models.generate_short_code, max_length=6, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipe', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='shortened_url', to='core.recipe')),
            ],
        ),
    ]
