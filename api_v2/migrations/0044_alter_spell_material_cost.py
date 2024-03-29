# Generated by Django 3.2.20 on 2024-02-28 22:35

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0043_remove_spell_material_cost_txt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spell',
            name='material_cost',
            field=models.DecimalField(decimal_places=2, default=None, help_text='Number representing the cost of the materials of the spell.', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
