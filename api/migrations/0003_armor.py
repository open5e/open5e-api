# Generated by Django 2.1.11 on 2019-10-28 21:03

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_document_copyright'),
    ]

    operations = [
        migrations.CreateModel(
            name='Armor',
            fields=[
                ('slug', models.SlugField(default=uuid.uuid1, primary_key=True, serialize=False, unique=True)),
                ('name', models.TextField()),
                ('desc', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.TextField()),
                ('cost', models.TextField()),
                ('weight', models.TextField()),
                ('stealth_disadvantage', models.BooleanField()),
                ('base_ac', models.IntegerField()),
                ('plus_dex_mod', models.BooleanField()),
                ('plus_con_mod', models.BooleanField()),
                ('plus_wis_mod', models.BooleanField()),
                ('plus_flat_mod', models.IntegerField()),
                ('plus_max', models.IntegerField()),
                ('strength_requirement', models.IntegerField()),
                ('route', models.TextField(default='armor/')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Document')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
