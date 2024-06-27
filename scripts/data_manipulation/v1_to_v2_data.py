
from django.template.defaultfilters import slugify

import json

from api_v2 import models as v2_models

from api.models import Monster as v1_model
from api_v2.models import Creature as v2_model


# Transformation function.

# Summarize the changes, print output.

# Write or not (opt in to write).


def main():
    v1_iteration = 0
    v1v2_match_count = 0
    v1_unmatch_count = 0
    v2_added_count = 0
    # CHANGE MODEL ON THIS LINE
    for obj_v1 in v1_model.objects.all():
        v1_iteration +=1
        computed_v2_key = get_v2_key_from_v1_obj(obj_v1)

        obj_v2 = v2_model.objects.filter(key=computed_v2_key).first()
        if obj_v2 is not None:
            v1v2_match_count +=1

        ### START LOGIC FOR PARSING V1 DATA ###

        if obj_v2 is None:
            print(obj_v1.slug, obj_v1.document.slug)
            obj_v2_document = v2_models.Document.objects.get(key=get_v2_doc_from_v1_obj(v1_obj=obj_v1))

            obj_v2 = v2_model(
                key=get_v2_key_from_v1_obj(v1_obj=obj_v1),
                name=obj_v1.name,
                document = obj_v2_document,
                size=get_v2_size_from_v1_obj(v1_obj=obj_v1),
                type=get_v2_type_from_v1_obj(v1_obj=obj_v1),
                category="Monsters",
                alignment = get_alignment(v1_obj=obj_v1)

            )
            copy_v2_speed_from_v1_creature(v1_obj=obj_v1, v2_obj=obj_v2)
            obj_v2.full_clean()
            v2_added_count +=1
 

        ### DO VALIDATION OF THE OBJECT
        #obj_v2.full_clean()
        # CAREFUL
         
        # END CAREFUL


    print("Performed {} iterations of v1 objects.".format(str(v1_iteration)))
    print("Matched {} v2 objects.".format(str(v1v2_match_count)))
    print("Added {} v2 objects".format(str(v2_added_count)))
    #print("Failed to match {} objects.".format(str(v1_unmatch_count)))

def _do_spell_distance(obj_v2):
    get_distance_and_unit_from_range_text(obj_v2)
    obj_v2.range = get_distance_and_unit_from_range_text(obj_v2)[0]
    obj_v2.range_unit = get_distance_and_unit_from_range_text(obj_v2)[1]
    
def _do_duration_remap(obj_v2):
    if obj_v2.key == "deepm_bottled-arcana":
        obj_v2.duration = '24 hours'
    if obj_v2.key == "deepm_delay-potion":
        obj_v2.duration = '1 hour'
    if obj_v2.key == "deepm_word-of-misfortune":
        obj_v2.duration = "1 minute"
    if obj_v2.key == "wz_eternal-echo":
        obj_v2.duration = "special"
    if obj_v2.key == "kp_blood-strike":
        obj_v2.duration = "special"

    if obj_v2.duration.lstrip()!=obj_v2.duration:
        obj_v2.duration = obj_v2.duration.lstrip()
    
def get_v2_key_from_v1_obj(v1_obj):
    v2_doc = get_v2_doc_from_v1_obj(v1_obj)
    v2_key = "{}_{}".format(slugify(v2_doc),slugify(v1_obj.name))
    return v2_key

def get_v2_doc_from_v1_obj(v1_obj):
    doc_lookup = {
        'a5e':'a5e-ag',
        'cc':'ccdx',
        'blackflag':'blkflg',
        'dmag':'deepm',
        'dmag-e':'deepmx',
        'kp':'kp',
        'menagerie':'mmenag',
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
    }
    return doc_lookup[v1_obj.document.slug]

def get_v2_type_from_v1_obj(v1_obj):
    undead = ['bonecollective-tob1-2023','boneswarm-tob1-2023','swarmofwolfspirits-tob1-2023']
    constructs = ['clockworkbeetleswarm-tob1-2023']
    monstrosity = ['cobbleswarm-tob1-2023']
    beast = ['deathbutterflyswarm-tob1-2023','greaterdeathbutterflyswarm-tob1-2023','swarmofmanabanescarabs-tob1-2023','swarmofprismaticbeetles-tob1-2023','swarmofwharflings-tob1-2023']
    fiends = ['iaaffrat-tob1-2023']
    aberrations = ['oculoswarm-tob1-2023']
    elementals = ['swarmoffiredancers-tob1-2023']
    fey = ['swarmofsluaghs-tob1-2023']
    if v1_obj.slug in undead:
        return v2_models.CreatureType.objects.get(key="undead")
    if v1_obj.slug in constructs:
        return v2_models.CreatureType.objects.get(key="construct")
    if v1_obj.slug in monstrosity:
        return v2_models.CreatureType.objects.get(key="monstrosity")
    if v1_obj.slug in beast:
        return v2_models.CreatureType.objects.get(key="beast")
    if v1_obj.slug in fiends:
        return v2_models.CreatureType.objects.get(key="fiend")
    if v1_obj.slug in aberrations:
        return v2_models.CreatureType.objects.get(key="aberration")
    if v1_obj.slug in elementals:
        return v2_models.CreatureType.objects.get(key="elemental")
    if v1_obj.slug in fey:
        return v2_models.CreatureType.objects.get(key="fey")


    return v2_models.CreatureType.objects.get(key=v1_obj.type.lower())

def get_v2_size_from_v1_obj(v1_obj):
    if v1_obj.slug=='tarrasque-a5e':
        return v2_models.Size.objects.get(key='gargantuan')
    v2_size = v2_models.Size.objects.filter(key=v1_obj.size.lower()).first()
    if v2_size is None:
        print("No size found for {}".format(v1_obj.slug))
    return v2_size

def copy_v2_speed_from_v1_creature(v1_obj, v2_obj):
    if 'walk' not in v1_obj.speed_json:
        v2_obj.walk = 0.0

    else: v2_obj.walk = float(json.loads(v1_obj.speed_json)['walk'])
    

    if v1_obj.slug == 'werebear': # This should be split into multiple creature entries.
        v2_obj.walk = 30.0
        return

    if 'hover' in v1_obj.speed_json:
        v2_obj.hover = True

    if 'fly' in v1_obj.speed_json:
        v2_obj.fly = float(json.loads(v1_obj.speed_json)['fly'])
    
    if 'burrow' in v1_obj.speed_json:
        v2_obj.burrow = float(json.loads(v1_obj.speed_json)['burrow'])
    
    if 'climb' in v1_obj.speed_json:
        v2_obj.climb = float(json.loads(v1_obj.speed_json)['climb'])

    if 'swim' in v1_obj.speed_json:
        v2_obj.swim = float(json.loads(v1_obj.speed_json)['swim'])

    if v1_obj.slug == 'werebear':
        v2_obj.walk = 30.0

def get_distance_and_unit_from_range_text(spell):
    if spell.range_text == 'Self':
        return (0,None)
    if spell.range_text == 'Touch':
        return (0.1, None)
    if spell.range_text == 'Special':
        return (0.2,None)
    if spell.range_text == 'Sight':
        return (2020.0,'feet')
    if spell.range_text == 'Unlimited':
        return (999999.0,'miles')

    rt_split = spell.range_text.split(" ")
    if "feet" in rt_split:
        return (float(rt_split[0]),"feet")
    if "miles" in rt_split:
        return (float(rt_split[0]),"miles")
    if "mile" in rt_split:
        return (float(rt_split[0]),"miles")

    print ("Could not parse {}".format(spell.range_text))

def get_alignment(v1_obj):
    ce = ['aboleth-thrall-a5e','abominable-snowman-a5e','accursed-guardian-naga-a5e']
    if v1_obj.slug in ce:
        return "chaotic evil"
    if v1_obj.document.slug != 'menagerie':
        if v1_obj.alignment == "":
            return get_alignment_from_doppelganger(v1_obj)
    if v1_obj.document.slug == 'menagerie':
        return "chaotic evil"
    return v1_obj.alignment

def get_alignment_from_doppelganger(v1_obj):
    srd_equivalent_key = "srd_{}".format(slugify(v1_obj.name))
    d = v2_models.Creature.objects.get(key=srd_equivalent_key)
    return d.alignment

if __name__ == '__main__':
    main()