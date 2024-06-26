# Generated by Django 3.2.20 on 2024-06-19 14:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0095_document_distance_unit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spell',
            name='shape_magnitude',
            field=models.FloatField(help_text='Used to measure distance.', null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
