# Generated by Django 3.2.20 on 2024-08-06 20:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0038_alter_monster_bonus_actions_json'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='archetype',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='armor',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='background',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='charclass',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='condition',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='document',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='feat',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='magicitem',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='monster',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='plane',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='race',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='section',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='spell',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='spelllist',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='subrace',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='weapon',
            name='created_at',
        ),
    ]
