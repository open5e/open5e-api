from api_v2 import models as v2


# Run this by:
#$  python manage.py shell -c 'from scripts.data_manipulation.spell import casting_option_generate; casting_option_generate()'

def remapdmg():
    print("REMAPPING dmg FOR monsters")
    for w in v2.Weapon.objects.all():
        if w.damage_type_old is not None:
            for dt in v2.DamageType.objects.all():
                if w.damage_type_old.lower() == dt.key:
                    mapped_dt = dt
                    w.damage_type = mapped_dt
                    w.save()
                    print("key:{} dmg_old:{} dmg_new:{}".format(w.pk, w.damage_type_old, dt.key))
            