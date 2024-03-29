# Generated by Django 3.2.20 on 2023-08-18 12:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0006_rename_prerequisite_desc_feat_prerequisite'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeatBenefit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the item.', max_length=100)),
                ('desc', models.TextField(help_text='Description of the game content item. Markdown.')),
                ('feat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api_v2.feat')),
            ],
            options={
                'ordering': ['pk'],
                'abstract': False,
            },
        ),
    ]
