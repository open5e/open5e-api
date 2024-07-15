
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
            obj_v2 = obj_v1.as_v2_creature()
            obj_v2.save()

        ### START LOGIC FOR PARSING V1 DATA ###

        if obj_v2 is None:
            #print(obj_v1. name)
            #obj_v2 = obj_v1.as_v2_creature()
            #obj_v2.full_clean()
            
            #copy_v2_damage_from_v1_monsters(obj_v1,obj_v2) # This requires objects to exist.
            #copy_v2_languages_from_v1_monster(obj_v1,obj_v2) # This requires objects to exist.

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

def get_senses(v1_obj):
    senses = {
        'normal':10560.0,
        'blindsight':None,
        'truesight':None,
        'darkvision':None,
        'tremorsense':None,
    }

    for s in v1_obj.senses.split(','):
        digits = "0123456789"

        if 'darkvision' in s.lower():
            darkvision_distance = ""
            for c in s:
                if c in digits:
                    darkvision_distance+=c
            senses['darkvision'] = float(darkvision_distance)
        if 'blindsight' in s.lower():
            blindsight_distance = ""
            for c in s:
                if c in digits:
                    blindsight_distance+=c
            senses['blindsight'] = float(blindsight_distance)
        if 'truesight' in s.lower():
            truesight_distance = ""
            for c in s:
                if c in digits:
                    truesight_distance+=c
            senses['truesight'] = float(truesight_distance)
        if 'tremorsense' in s.lower():
            tremorsense_distance = ""
            for c in s:
                if c in digits:
                    tremorsense_distance+=c
            senses['tremorsense'] = float(tremorsense_distance)
        if 'blind beyond' in s.lower():
            senses['normal'] = None

    return senses

def copy_v2_scores_from_v1_creature(obj_v1, obj_v2):
    obj_v2.ability_score_strength = obj_v1.strength
    obj_v2.ability_score_dexterity = obj_v1.dexterity
    obj_v2.ability_score_constitution = obj_v1.constitution
    obj_v2.ability_score_intelligence = obj_v1.intelligence
    obj_v2.ability_score_wisdom = obj_v1.wisdom
    obj_v2.ability_score_charisma = obj_v1.charisma

def copy_v2_damage_from_v1_monsters(obj_v1,obj_v2):
    for di in obj_v1.damage_immunities.split(','):
        if v2_models.DamageType.objects.get(key=di.strip().lower()):
            obj_v2.damage_immunities.add(v2_models.DamageType.objects.get(key=di.strip().lower()))
    
    for di in obj_v1.damage_resistances.split(','):
        if v2_models.DamageType.objects.get(key=di.strip().lower()):
            obj_v2.damage_resistances.add(v2_models.DamageType.objects.get(key=di.strip().lower()))

    for di in obj_v1.damage_vulnerabilities.split(','):
        if v2_models.DamageType.objects.get(key=di.strip().lower()):
            obj_v2.damage_vulnerabilities.add(v2_models.DamageType.objects.get(key=di.strip().lower()))

def copy_v2_languages_from_v1_monsters(obj_v1,obj_v2):
    for l in obj_v1.languages.split(','):
        language_looked_up = v2_models.Language.objects.filter(pk=slugify(l.lower()))
        if len(language_looked_up)==1:
            obj_v2.languages.add(language_looked_up)
        if "all" in l:
            obj_v2.languages.add(v2_models.Language.objects.all())
    
        if "telepathy" in l:
            between_parens = l.split("(")[1].split(")")[0]
            distance = between_parens.split(" ")[0]
            obj_v2.telepathy_range = distance

            #parse telepathy range

    obj_v2.languages_desc = obj_v1.languages

    # cannot speak
    # description

def copy_v2_throws_from_v1_creature(obj_v1, obj_v2):
    obj_v2.saving_throw_strength = obj_v1.strength_save
    obj_v2.saving_throw_dexterity = obj_v1.dexterity_save
    obj_v2.saving_throw_constitution = obj_v1.constitution_save
    obj_v2.saving_throw_intelligence = obj_v1.intelligence_save
    obj_v2.saving_throw_wisdom = obj_v1.wisdom_save
    obj_v2.saving_throw_charisma = obj_v1.charisma_save

def copy_v2_skills_from_v1_creature(obj_v1, obj_v2):
    obj_v1.skills_json = obj_v1.skills_json.lower()
    obj_v2.skill_bonus_acrobatics = json.loads(obj_v1.skills_json).get('acrobatics')
    obj_v2.skill_bonus_animal_handling  = json.loads(obj_v1.skills_json).get('animal_handling')
    obj_v2.skill_bonus_arcana = json.loads(obj_v1.skills_json).get('arcana')
    obj_v2.skill_bonus_athletics = json.loads(obj_v1.skills_json).get('athletics')
    obj_v2.skill_bonus_deception = json.loads(obj_v1.skills_json).get('deception')
    obj_v2.skill_bonus_history = json.loads(obj_v1.skills_json).get('history')
    obj_v2.skill_bonus_insight = json.loads(obj_v1.skills_json).get('insight')
    obj_v2.skill_bonus_intimidation = json.loads(obj_v1.skills_json).get('intimidation')
    obj_v2.skill_bonus_investigation = json.loads(obj_v1.skills_json).get('investigation')
    obj_v2.skill_bonus_medicine = json.loads(obj_v1.skills_json).get('medicine')
    obj_v2.skill_bonus_nature = json.loads(obj_v1.skills_json).get('nature')
    obj_v2.skill_bonus_perception = json.loads(obj_v1.skills_json).get('perception')
    obj_v2.skill_bonus_performance = json.loads(obj_v1.skills_json).get('performance')
    obj_v2.skill_bonus_persuasion = json.loads(obj_v1.skills_json).get('persuasion')
    obj_v2.skill_bonus_religion = json.loads(obj_v1.skills_json).get('religion')
    obj_v2.skill_bonus_sleight_of_hand = json.loads(obj_v1.skills_json).get('sleight_of_hand')
    obj_v2.skill_bonus_stealth = json.loads(obj_v1.skills_json).get('stealth')
    obj_v2.skill_bonus_survival = json.loads(obj_v1.skills_json).get('survival')

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

def get_passive_perception(v1_obj):
    if "passive perception" in v1_obj.senses.lower():
        for s in v1_obj.senses.split(','):
            if "passive perception" in s:
                a_pp = s.split('passive perception')[1]
                trimmed = a_pp.replace("(","").replace(")","").replace(",","")
                return trimmed

    bonusx2 = v1_obj.wisdom - 10
    bonus = bonusx2 // 2
    return 10 + bonus

if __name__ == '__main__':
    main()