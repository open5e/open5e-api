from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_v2', '0078_merge_staging_and_crossreference_chains'),
    ]

    operations = [
        migrations.RenameField(
            model_name='creatureaction',
            old_name='order',
            new_name='order_in_statblock',
        ),
        migrations.RenameField(
            model_name='creatureaction',
            old_name='form_condition',
            new_name='limited_to_form',
        ),
        migrations.RenameField(
            model_name='creatureaction',
            old_name='legendary_cost',
            new_name='legendary_action_cost',
        ),
    ]
