# Generated by Django 3.2.20 on 2024-03-15 12:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0070_spell_school'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='spell',
            name='school_old',
        ),
    ]
