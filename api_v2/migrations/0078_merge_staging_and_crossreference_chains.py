# Merge migration: reconciles staging item/creature chain with feature crossreference chain.
# Staging leaf: 0074_alter_creature_challenge_rating
# Feature leaf: 0077_alter_crossreference_options
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0074_alter_creature_challenge_rating'),
        ('api_v2', '0077_alter_crossreference_options'),
    ]

    operations = [
    ]
