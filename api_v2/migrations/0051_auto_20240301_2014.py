# Generated by Django 3.2.20 on 2024-03-01 20:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0050_remove_castingoption_target_count_txt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spell',
            name='duration',
            field=models.TextField(choices=[('instantaneous', 'instantaneous'), ('instantaneous or special', 'instantaneous or special'), ('1 turn', '1 turn'), ('1 round', '1 round'), ('concentration + 1 round', 'concentration + 1 round'), ('2 rounds', '2 rounds'), ('3 rounds', '3 rounds'), ('4 rounds', '4 rounds'), ('1d4+2 round', '1d4+2 round'), ('5 rounds', '5 rounds'), ('6 rounds', '6 rounds'), ('10 rounds', '10 rounds'), ('up to 1 minute', 'up to 1 minute'), ('1 minute', '1 minute'), ('1 minute, or until expended', '1 minute, or until expended'), ('1 minute, until expended', '1 minute, until expended'), ('1 minute', '1 minute'), ('5 minutes', '5 minutes'), ('10 minutes', '10 minutes'), ('1 minute or 1 hour', '1 minute or 1 hour'), ('up to 1 hour', 'up to 1 hour'), ('1 hour', '1 hour'), ('1 hour or until triggered', '1 hour or until triggered'), ('2 hours', '2 hours'), ('3 hours', '3 hours'), ('1d10 hours', '1d10 hours'), ('6 hours', '6 hours'), ('2-12 hours', '2-12 hours'), ('up to 8 hours', 'up to 8 hours'), ('8 hours', '8 hours'), ('1 hour/caster level', '1 hour/caster level'), ('10 hours', '10 hours'), ('12 hours', '12 hours'), ('24 hours or until the target attempts a third death saving throw', '24 hours or until the target attempts a third death saving throw'), ('24 hours', '24 hours'), ('1 day', '1 day'), ('3 days', '3 days'), ('5 days', '5 days'), ('7 days', '7 days'), ('10 days', '10 days'), ('13 days', '13 days'), ('30 days', '30 days'), ('1 year', '1 year'), ('special', 'special'), ('until dispelled or destroyed', 'until dispelled or destroyed'), ('until destroyed', 'until destroyed'), ('until dispelled', 'until dispelled'), ('until cured or dispelled', 'until cured or dispelled'), ('until dispelled or triggered', 'until dispelled or triggered'), ('permanent until discharged', 'permanent until discharged'), ('permanent; one generation', 'permanent; one generation'), ('permanent', 'permanent')], help_text='Description of the duration of the effect such as "instantaneous" or "1 minute"'),
        ),
        migrations.AlterField(
            model_name='spell',
            name='material_cost',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, help_text='Number representing the cost of the materials of the spell.', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='spell',
            name='range',
            field=models.TextField(choices=[('Self', 'Self'), ('Touch', 'Touch'), ('Special', 'Special'), ('5 feet', '5 feet'), ('10 feet', '10 feet'), ('15 feet', '15 feet'), ('20 feet', '20 feet'), ('25 feet', '25 feet'), ('30 feet', '30 feet'), ('40 feet', '40 feet'), ('50 feet', '50 feet'), ('60 feet', '60 feet'), ('90 feet', '90 feet'), ('100 feet', '100 feet'), ('120 feet', '120 feet'), ('150 feet', '150 feet'), ('180 feet', '180 feet'), ('200 feet', '200 feet'), ('300 feet', '300 feet'), ('400 feet', '400 feet'), ('500 feet', '500 feet'), ('1000 feet', '1000 feet'), ('Sight', 'Sight'), ('1 mile', '1 mile'), ('5 miles', '5 miles'), ('10 miles', '10 miles'), ('100 miles', '100 miles'), ('150 miles', '150 miles'), ('500 miles', '500 miles'), ('Unlimited', 'Unlimited')], help_text='Spell target range.'),
        ),
    ]
