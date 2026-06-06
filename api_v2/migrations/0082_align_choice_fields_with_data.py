from django.db import migrations, models

DIE_TYPE_CHOICES = [
    ("D3", "d3"),
    ("D4", "d4"),
    ("D6", "d6"),
    ("D8", "d8"),
    ("D10", "d10"),
    ("D12", "d12"),
    ("D20", "d20"),
    ("d3", "d3"),
    ("d4", "d4"),
    ("d6", "d6"),
    ("d8", "d8"),
    ("d10", "d10"),
    ("d12", "d12"),
    ("d20", "d20"),
]

DISTANCE_UNIT_CHOICES = [
    ("feet", "feet"),
    ("ft", "ft"),
    ("miles", "miles"),
    ("any", "any"),
]

WEIGHT_UNIT_CHOICES = [
    ("lb", "lb"),
    ("kg", "kg"),
]

FEAT_TYPE_CHOICES = [
    ("GENERAL", "General"),
    ("ORIGIN", "Origin"),
    ("FIGHTING_STYLE", "Fighting Style"),
    ("EPIC_BOON", "Epic Boon"),
    ("General", "General"),
    ("Origin", "Origin"),
    ("Fighting Style", "Fighting Style"),
    ("Epic Boon", "Epic Boon"),
]

CREATURE_USES_TYPE_CHOICES = [
    ("PER_DAY", "X/Day"),
    ("RECHARGE", "Recharge"),
    ("RECHARGE_ON_ROLL", "Recharge X-6"),
    ("RECHARGE_AFTER_REST", "Recharge after a Short or Long rest"),
]

CASTER_TYPE_CHOICES = [
    ("FULL", "Full"),
    ("HALF", "Half"),
    ("PACT", "Pact"),
    ("NONE", "None"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("api_v2", "0081_creature_desc"),
    ]

    operations = [
        migrations.AlterField(
            model_name="characterclass",
            name="caster_type",
            field=models.CharField(
                blank=True,
                choices=CASTER_TYPE_CHOICES,
                default=None,
                help_text="Type of caster. Options are full, half, none.",
                max_length=100,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="characterclass",
            name="hit_dice",
            field=models.CharField(
                blank=True,
                choices=DIE_TYPE_CHOICES,
                default=None,
                help_text="Dice notation hit dice option.",
                max_length=100,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="creature",
            name="unit",
            field=models.CharField(
                blank=True,
                choices=DISTANCE_UNIT_CHOICES,
                help_text="What distance unit the relevant field uses.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="creatureaction",
            name="uses_type",
            field=models.CharField(
                blank=True,
                choices=CREATURE_USES_TYPE_CHOICES,
                help_text="How use of the action is limited, if at all.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="creatureactionattack",
            name="damage_die_type",
            field=models.CharField(
                blank=True,
                choices=DIE_TYPE_CHOICES,
                help_text="What kind of die to roll for damage.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="creatureactionattack",
            name="distance_unit",
            field=models.CharField(
                blank=True,
                choices=DISTANCE_UNIT_CHOICES,
                help_text="What distance unit the relevant field uses.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="creatureactionattack",
            name="extra_damage_die_type",
            field=models.CharField(
                blank=True,
                choices=DIE_TYPE_CHOICES,
                help_text="What kind of die to roll for damage.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="document",
            name="distance_unit",
            field=models.CharField(
                blank=True,
                choices=DISTANCE_UNIT_CHOICES,
                help_text="What distance unit the relevant field uses.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="document",
            name="weight_unit",
            field=models.CharField(
                blank=True,
                choices=WEIGHT_UNIT_CHOICES,
                help_text="What weight unit the relevant field uses.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="feat",
            name="type",
            field=models.CharField(
                choices=FEAT_TYPE_CHOICES,
                default="GENERAL",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="size",
            name="distance_unit",
            field=models.CharField(
                blank=True,
                choices=DISTANCE_UNIT_CHOICES,
                help_text="What distance unit the relevant field uses.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="size",
            name="suggested_hit_dice",
            field=models.CharField(
                blank=True,
                choices=DIE_TYPE_CHOICES,
                help_text="What kind of die to roll for damage.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="spell",
            name="range_text",
            field=models.TextField(help_text="Spell target range."),
        ),
        migrations.AlterField(
            model_name="spell",
            name="range_unit",
            field=models.CharField(
                blank=True,
                choices=DISTANCE_UNIT_CHOICES,
                help_text="What distance unit the relevant field uses.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="spell",
            name="shape_size_unit",
            field=models.CharField(
                blank=True,
                choices=DISTANCE_UNIT_CHOICES,
                help_text="What distance unit the relevant field uses.",
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="weapon",
            name="distance_unit",
            field=models.CharField(
                blank=True,
                choices=DISTANCE_UNIT_CHOICES,
                help_text="What distance unit the relevant field uses.",
                max_length=20,
                null=True,
            ),
        ),
    ]
