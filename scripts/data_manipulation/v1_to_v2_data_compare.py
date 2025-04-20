
from django.template.defaultfilters import slugify

import json

from api_v2 import models as v2_models
from api import models as v1_models

def main():
    for v1_doc in v1_models.Document.objects.all():
        print("DOCUMENT: {}".format(v1_doc.slug))
        v2_doc = v2_models.Document.objects.get(key=get_v2_doc_from_v1_doc(v1_doc))

        # Creature Comparison
        v1_doc_monster_count = v1_models.Monster.objects.filter(document__slug=v1_doc.slug).count()
        v2_doc_creature_count = v2_models.Creature.objects.filter(document__key=v2_doc.key).count()
        print_comparison("Creature",v1_doc=v1_doc,v2_doc=v2_doc,v1_count=v1_doc_monster_count,v2_count=v2_doc_creature_count)

        # Spell Comparison
        v1_doc_spell_count = v1_models.Spell.objects.filter(document__slug=v1_doc.slug).count()
        v2_doc_spell_count = v2_models.Spell.objects.filter(document__key=v2_doc.key).count()
        print_comparison("Spell",v1_doc=v1_doc,v2_doc=v2_doc,v1_count=v1_doc_spell_count,v2_count=v2_doc_spell_count)

        # Feat Comparison
        v1_doc_feat_count = v1_models.Feat.objects.filter(document__slug=v1_doc.slug).count()
        v2_doc_feat_count = v2_models.Feat.objects.filter(document__key=v2_doc.key).count()
        print_comparison("Feat",v1_doc=v1_doc,v2_doc=v2_doc,v1_count=v1_doc_feat_count,v2_count=v2_doc_feat_count)

        # Race Comparison
        v1_doc_race_count = v1_models.Race.objects.filter(document__slug=v1_doc.slug).count()
        v2_doc_race_count = v2_models.Race.objects.filter(document__key=v2_doc.key,subrace_of=None).count() # Filter out subraces.
        print_comparison("Race",v1_doc=v1_doc,v2_doc=v2_doc,v1_count=v1_doc_race_count,v2_count=v2_doc_race_count)

        # SubRace Comparison
        v1_doc_subrace_count = v1_models.Subrace.objects.filter(document__slug=v1_doc.slug).count()
        v2_doc_subrace_count = v2_models.Race.objects.filter(document__key=v2_doc.key,subrace_of__isnull=False).count() # Filter out subraces.
        print_comparison("Subrace",v1_doc=v1_doc,v2_doc=v2_doc,v1_count=v1_doc_subrace_count,v2_count=v2_doc_subrace_count)

        # Background Comparison
        v1_doc_bg_count = v1_models.Background.objects.filter(document__slug=v1_doc.slug).count()
        v2_doc_bg_count = v2_models.Background.objects.filter(document__key=v2_doc.key).count() # Filter out subraces.
        print_comparison("Background",v1_doc=v1_doc,v2_doc=v2_doc,v1_count=v1_doc_bg_count,v2_count=v2_doc_bg_count)

        # Class Comparison
        v1_doc_c_count = v1_models.CharClass.objects.filter(document__slug=v1_doc.slug).count()
        v2_doc_c_count = v2_models.CharacterClass.objects.filter(document__key=v2_doc.key, subclass_of=None).count() # Filter out subraces.
        print_comparison("CharClass",v1_doc=v1_doc,v2_doc=v2_doc,v1_count=v1_doc_c_count,v2_count=v2_doc_c_count)

        # Subclass Comparison
        v1_doc_sc_count = v1_models.Archetype.objects.filter(document__slug=v1_doc.slug).count()
        v2_doc_sc_count = v2_models.CharacterClass.objects.filter(document__key=v2_doc.key, subclass_of__isnull=False).count() # Filter out subraces.
        print_comparison("SubClass",v1_doc=v1_doc,v2_doc=v2_doc,v1_count=v1_doc_sc_count,v2_count=v2_doc_sc_count)




def get_v2_doc_from_v1_doc(v1_doc):
    doc_lookup = {
        'a5e':'a5e-ag',
        'cc':'ccdx',
        'blackflag':'blkflg',
        'dmag':'deepm',
        'dmag-e':'deepmx',
        'kp':'kp',
        'menagerie':'a5e-mm',
        'o5e':'open5e',
        'taldorei':'tdcs',
        'tob':'tob',
        'tob-2023':'tob-2023',
        'tob2':'tob2',
        'tob3':'tob3',
        'toh':'toh',
        'vom':'vom',
        'warlock':'wz',
        'wotc-srd':'srd',
        'blackflag':'bfrd'
    }

    return doc_lookup[v1_doc.slug]

def is_within_5pct(num1,num2):
    if num1==0: return True
    num1_upper = num1*1.05
    num1_lower = num1*0.95

    return num2 < num1_upper and num2 > num1_lower

def print_comparison(type,v1_doc,v2_doc,v1_count,v2_count):
    status=('\033[91m',"NOT_OK")
    if is_within_5pct(v1_count,v2_count): status=('\033[92m',"OK")
    
    print("{}{}: {}: {} to {}: {} / {}{}".format(
            status[0],
            status[1],
            type,
            v1_doc.slug,
            v2_doc.key,
            v1_count,
            v2_count,
            '\x1b[0m'
        ))



if __name__ == '__main__':
    main()