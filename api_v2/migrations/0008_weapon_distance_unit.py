# Generated by Django 5.1.1 on 2024-10-09 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0007_rename_range_long_weapon_long_range_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='weapon',
            name='distance_unit',
            field=models.CharField(blank=True, choices=[('feet', 'feet'), ('miles', 'miles')], help_text='What distance unit the relevant field uses.', max_length=20, null=True),
        ),
    ]