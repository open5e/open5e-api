# Generated by Django 5.1.2 on 2024-10-22 14:04

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0009_merge_20241010_0144'),
    ]

    operations = [
        migrations.AddField(
            model_name='spellcastingoption',
            name='concentration',
            field=models.BooleanField(blank=True, help_text='Whether the effect requires concentration to be maintained.', null=True),
        ),
        migrations.AddField(
            model_name='spellcastingoption',
            name='shape_size',
            field=models.FloatField(blank=True, help_text='Used to measure distance.', null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
