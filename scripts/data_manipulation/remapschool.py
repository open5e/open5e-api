from api import models as v1
from api_v2 import models as v2


# Run this by:
#$  python manage.py shell -c 'from scripts.data_manipulation.spell import casting_option_generate; casting_option_generate()'

def remapschool():
    print("REMAPPING RARITY FOR ITEMS")
    for spell in v2.Spell.objects.all():
        spell_v1 = v1.Spell.objects.filter(slug=spell.key).first()
                         
        print("key:{} v2school:{} v1school:{}".format(spell.key,spell.school,spell_v1.school))

        spell.school = v2.SpellSchool.objects.get(key=spell_v1.school.lower())
        spell.save()
            #spell.school = ss
            #spell.school.save()

