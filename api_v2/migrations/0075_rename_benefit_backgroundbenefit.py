# Generated by Django 3.2.20 on 2024-05-24 14:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0074_rename_background_benefit_parent'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Benefit',
            new_name='BackgroundBenefit',
        ),
    ]
