# Generated by Django 3.2.20 on 2023-10-04 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0015_auto_20231003_2015'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='characteristics',
            name='background',
        ),
        migrations.AlterField(
            model_name='featbenefit',
            name='desc',
            field=models.TextField(help_text='Description of the game content item. Markdown.'),
        ),
        migrations.DeleteModel(
            name='BackgroundFeature',
        ),
        migrations.DeleteModel(
            name='Characteristics',
        ),
    ]
