from api_v2 import models as v2


# Run this by:
#$  python manage.py shell -c 'from scripts.data_manipulation.spell import casting_option_generate; casting_option_generate()'

def remapschool():
    print("REMAPPING RARITY FOR ITEMS")
    for spell in v2.Spell.objects.all():
        for ss in v2.SpellSchool.objects.all():
            if spell.school_old == ss.key:
                mapped_s = ss
            
                print("key:{} size_int:{} mapped_size:{}".format(spell.key,spell.school_old,mapped_s.name))
                spell.school = ss
                spell.school.save()

