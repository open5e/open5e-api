# Generated by Django 3.2.20 on 2024-02-28 22:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0042_spell_material_cost'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='spell',
            name='material_cost_txt',
        ),
    ]