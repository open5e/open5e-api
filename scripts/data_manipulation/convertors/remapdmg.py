from api_v2 import models as v2


# Run this by:
#$  python manage.py shell -c 'from scripts.data_manipulation.spell import casting_option_generate; casting_option_generate()'

def remapdmg():
    print("REMAPPING dmg FOR monsters")
    for ca in v2.CreatureAttack.objects.all():
        if ca.extra_damage_type_OLD is not None:
            for dt in v2.DamageType.objects.all():
                if ca.extra_damage_type_OLD.lower() == dt.key:
                    mapped_dt = dt
                    ca.extra_damage_type = mapped_dt
                    ca.save()
                    print("key:{} dmg_old:{} dmg_new:{}".format(ca.pk, ca.extra_damage_type_OLD, dt.key))
            