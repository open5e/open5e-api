# Generated by Django 3.2.20 on 2023-10-29 11:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0009_alter_creatureaction_options'),
    ]

    operations = [
        migrations.RenameField(
            model_name='creature',
            old_name='type',
            new_name='deprecated_type',
        ),
    ]
