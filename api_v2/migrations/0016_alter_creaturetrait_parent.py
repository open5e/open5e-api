# Generated by Django 5.1.2 on 2024-11-17 11:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0015_creature_environments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creaturetrait',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='traits', to='api_v2.creature'),
        ),
    ]
