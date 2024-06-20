
from django.template.defaultfilters import slugify

from api.models import Spell as v1_model
from api_v2.models import Spell as v2_model


# Transformation function.

# Summarize the changes, print output.

# Write or not (opt in to write).


def main():
    v1_iteration = 0
    v1v2_match_count = 0
    v1_unmatch_count = 0
    # CHANGE MODEL ON THIS LINE
    for obj_v1 in v1_model.objects.all():
        v1_iteration +=1
        computed_v2_key = get_v2_key_from_v1_obj(obj_v1)

        obj_v2 = v2_model.objects.filter(key=computed_v2_key).first()
        if obj_v2 is None:
            v1_unmatch_count +=1
            continue
        v1v2_match_count +=1

        ### START LOGIC FOR PARSING V1 DATA ###

        _do_spell_distance(obj_v2=obj_v2)
        _do_duration_remap(obj_v2=obj_v2)

        ### DO VALIDATION OF THE OBJECT
        obj_v2.full_clean()
        # CAREFUL
        obj_v2.save()
        # END CAREFUL


    print("Performed {} iterations of v1 objects.".format(str(v1_iteration)))
    print("Matched {} v2 objects.".format(str(v1v2_match_count)))
    print("Failed to match {} objects.".format(str(v1_unmatch_count)))

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

if __name__ == '__main__':
    main()