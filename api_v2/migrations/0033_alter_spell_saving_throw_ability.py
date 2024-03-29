# Generated by Django 3.2.20 on 2024-02-09 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0032_alter_spell_damage_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spell',
            name='saving_throw_ability',
            field=models.TextField(default='', help_text='Given the spell requires a saving throw, which ability is targeted. Empty string if no saving throw.'),
        ),
    ]
