# Generated by Django 3.2.20 on 2024-02-29 20:04

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0045_auto_20240229_2003'),
    ]

    operations = [
        migrations.AddField(
            model_name='spell',
            name='target_count',
            field=models.IntegerField(help_text='Integer representing the count of targets.', null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
