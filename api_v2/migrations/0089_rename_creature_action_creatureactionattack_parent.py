# Generated by Django 3.2.20 on 2024-06-01 13:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0088_auto_20240601_1332'),
    ]

    operations = [
        migrations.RenameField(
            model_name='creatureactionattack',
            old_name='creature_action',
            new_name='parent',
        ),
    ]