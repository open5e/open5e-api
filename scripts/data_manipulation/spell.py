from api import models as v1
from api_v2 import models as v2


def spellmigrate(save=False):
    success_count=0
    fail_list=[]
    failed=False
    for v1_spell in v1.Spell.objects.all():
        map1to2(v1_spell)
        success_count+=1
        if failed:
            print("{} failed to map.".format(v1_spell.slug))

    print("{} spells mapped all fields successfully.".format(success_count))
    

def map1to2(v1_spell):
    # Get documents, and map them.

    # Select target type.

    # Fit Action into the correct size.


    v2.Spell(
        key=v1_spell.slug,
        name=v1_spell.name,
        desc=v1_spell.desc,
        document=doc1to2(v1_spell.document),
        level=v1_spell.spell_level,
        range=v1_spell.range.lower(), 
        verbal=v1_spell.requires_verbal_components,
        somatic=v1_spell.requires_somatic_components,
        material=v1_spell.requires_material_components,
        material_specified=get_material_specified(v1_spell.material),
        material_cost=get_material_cost(v1_spell.material),
        ritual=v1_spell.can_be_cast_as_ritual,
        casting_time=get_casting_time(v1_spell.casting_time),
        target_type=get_target(v1_spell.desc)[0],
        target_count=get_target(v1_spell.desc)[1],
        saving_throw_ability=get_saving_throw_ability(v1_spell.desc),
        damage_roll="",
        duration="",
        shape_type="cone",
        shape_magnitude=10
    ).clean_fields()


def doc1to2(v1_doc):
    doc_map = {
        "wotc-srd":"srd",
        "toh":"toh",
        "vom":"vault-of-magic",
        "taldorei":"taldorei",
        "o5e":"a5esrd"}

    return v2.Document.objects.get(pk=doc_map[v1_doc.slug])


def get_target(desc):
    # Returns one of "point", 

    types=['creature','object','point','area']
    count_options=[[], # Zero
    ["a","one"], # One
    ["two", "a pair of", "up to two"], #Two
    ["three", "up to three"],
    ["four", "up to four"],
    ["five", "up to five"],
    ["six", "up to six"],
    [], # Seven
    ["eight", "up to eight"],
    [],[],[],
    ["twelve", "up to twelve"]
    ]
    
    for i, word in enumerate(desc.split(" ")):
        target_count=1
        word = word.lower()
        prevword = desc.split(" ")[i-1]
        if word.endswith("s"):
            word=word[:-1]
            for idx,co in enumerate(count_options):
                if prevword in co:
                    target_count=idx
        if word in types:
            return (word, target_count)
    
    return (None, None)


def get_casting_time(v1_casting_time):
    for CTC in v2.enums.CASTING_TIME_CHOICES:
        if v1_casting_time.split(" ")[1] == CTC[1].lower():
            return CTC[0]
    print(v1_casting_time)


def get_material_cost(v1_material):
    if v1_material.find("GP") >= 0:
        c=v1_material.split("GP")[0].split(" ")[-1]
        return c + " GP"
    # Need to handle commas in the amount, and lack of space.
    # 1,000gp
    # 1,000 gp
    # 25gp
    return "0 GP"


def get_saving_throw_ability(desc):
    abilities = [
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma"
    ]
    if desc.find("saving throw") >= 0:
        # There is a saving throw reference.
        for idx, word in enumerate(desc.split(" ")):
            prevword = desc.split(" ")[idx-1]
            if prevword.lower() in abilities:
                return prevword.lower()
    return ""


def get_damage_roll(desc):
    return None

def get_shape(desc):
    
    return (None, None)