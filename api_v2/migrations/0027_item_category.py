# Generated by Django 3.2.20 on 2023-11-05 00:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0026_auto_20231105_0015'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api_v2.itemcategory'),
        ),
    ]
