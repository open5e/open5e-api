# Generated by Django 3.2.18 on 2023-05-11 17:41

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0025_auto_20230423_0234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spell',
            name='target_range_sort',
            field=models.IntegerField(help_text='Sortable distance ranking to the target. 0 for self, 1 for touch, sight is 9999, unlimited (same plane) is 99990, unlimited any plane is 99999. All other values in feet.', validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.CreateModel(
            name='SpellList',
            fields=[
                ('slug', models.CharField(default=uuid.uuid1, help_text='Short name for the game content item.', max_length=255, primary_key=True, serialize=False, unique=True)),
                ('name', models.TextField(help_text='Name of the game content item.')),
                ('desc', models.TextField(help_text='Description of the game content item. Markdown.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('page_no', models.IntegerField(null=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.document')),
                ('spells', models.ManyToManyField(help_text='The set of spells.', to='api.Spell')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
