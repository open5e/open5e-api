# Generated by Django 3.2.20 on 2024-03-15 12:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0061_rename_damage_type_creatureattack_damage_type_old'),
    ]

    operations = [
        migrations.AddField(
            model_name='creatureattack',
            name='damage_type',
            field=models.ForeignKey(help_text='What kind of damage this attack deals', null=True, on_delete=django.db.models.deletion.CASCADE, to='api_v2.damagetype'),
        ),
    ]
