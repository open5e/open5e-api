# Generated by Django 5.1.2 on 2024-10-24 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0011_merge_20241022_1426'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creature',
            name='subcategory',
            field=models.CharField(blank=True, help_text='What subcategory this creature belongs to.', max_length=100, null=True),
        ),
    ]