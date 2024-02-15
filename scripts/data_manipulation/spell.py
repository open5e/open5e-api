from api import models as v1
from api_v2 import models as v2




def spellmigrate(save=False):
    success_count=0
    fail_list=[]
    failed=False
    for v1_spell in v1.Spell.objects.all():

        #map1to2(v1_spell)
        try:
            map1to2(v1_spell)

            success_count+=1
        except Exception as e:
            print("Succeeded on {} spells".format(success_count))
            failed=True
            print("Failed importing of: : '{}'".format(v1_spell.pk))
            print("Try link: : https://open5e.com/spells/{}".format(v1_spell.pk))
            print(e)
            
            exit(1)
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
        range=get_range(v1_spell.range.lower(), v1_spell.pk),
        verbal=v1_spell.requires_verbal_components,
        somatic=v1_spell.requires_somatic_components,
        material=v1_spell.requires_material_components,
        material_specified=v1_spell.material,
        material_cost=get_material_cost(v1_spell.material),
        ritual=v1_spell.can_be_cast_as_ritual,
        casting_time=get_casting_time(v1_spell.casting_time),
        target_type=get_target(v1_spell.desc,v1_spell.slug,v1_spell.range)[0],
        target_count=get_target(v1_spell.desc,v1_spell.slug,v1_spell.range)[1],
        saving_throw_ability=get_saving_throw_ability(v1_spell.desc),
        damage_roll=get_damage(v1_spell.desc)[0],
        damage_types=["hi"],
        duration=v1_spell.duration.lower(),
        shape_type="cone",
        shape_magnitude=10
    ).clean_fields()


def doc1to2(v1_doc):
    doc_map = {
        "wotc-srd":"srd",
        "toh":"toh",
        "vom":"vault-of-magic",
        "taldorei":"taldorei",
        "a5e":"a5esrd",
        "dmag":"deep-magic",
        "warlock":"warlock",
        "dmag-e":"dmag-e",
        "kp":'kp',
        "o5e":"o5e"}

    return v2.Document.objects.get(pk=doc_map[v1_doc.slug])


def get_target(desc, v1_pk, v1_range):
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
        word = word.lower().strip(".").strip(",")
        prevword = desc.split(" ")[i-1]
        if word.endswith("s"):
            word=word[:-1]
            for idx,co in enumerate(count_options):
                if prevword in co:
                    target_count=idx
        if word in types:
            return (word, target_count)
        if word == "weapon" and prevword == "nonmagical":
            return ("object", target_count)
    
    creature_exception_list = ["While casting this spell, you must engage your target in conversation", "Make a ranged spell attack", "Make a melee spell attack","Make a ranged spell attack against the target"]
    creature2_exception_list = ["A stinking bubble of acid is conjured out of thin air to fly at the targets, dealing 1d6 acid damage"]
    for sentence in desc.split("."):
        if sentence.strip() in creature_exception_list:
            return("creature",1)
        if sentence.strip() in creature2_exception_list:
            return("creature",2)

    # Creature opt-ins
    if v1_range == "self" or v1_range == "Self":
        return("creature",1)
    if v1_pk.startswith(("animal-friendship", "arcane-muscles", "aspect-of-the-moon","continual-flame","chain-lightning","charm-monster","charm-person","clone",'darkvision','detect-magic','freedom-of-movement','greater-invisibility','guidance',"hideous-laughter",'hold-monster','hold-person')):
        return("creature",1)
    if v1_pk.startswith(('longstrider','mage-armor','mind-blank','phantasmal-killer',"mindshield","planar-binding","protection-from-energy","protection-from-poison","reincarnate","resistance")):
        return("creature",1)
    if v1_pk.startswith(('sacred-flame','spare-the-dying','speak-with-dead','spider-climb','stoneskin','true-seeing',"vicious-mockery",'broken-charge')):
        return("creature",1)
    if v1_pk in ["afflict-line","alter-arrows-fortune",'arcane-sight','black-goats-blessing','black-hand',"candles-insight",'claws-of-the-earth-dragon','curse-of-the-grave','distracting-divination','gremlins','machine-sacrifice','mechanical-union','strength-of-the-underworld','tick-stop','winding-key','write-memory']:
        return("creature",1)
    if v1_pk in []:
        return("creature",1)
    if v1_pk in ["bane-a5e","bless-a5e",'magic-missile-a5e',"scorching-ray-a5e",'darkbolt','thunderous-stampede','scorching-ray']:
        return("creature",3)
    if v1_pk.startswith(("barkskin-a5e","bestow-curse-a5e","blindnessdeafness-a5e","finger-of-death-a5e","fly-a5e",'geas-a5e',"gentle-repose","inflict-wounds-a5e","invigorated-strikes-a5e","irresistible-dance-a5e","jump-a5e","lesser-restoration-a5e",'sending-a5e','shield-of-faith-a5e',"shocking-grasp-a5e",'greater-maze','harry','insightful-maneuver','lesser-maze','molechs-blessing')):
        return("creature",1)
    if v1_pk in ['maddening-whispers','monstrous-empathy','outflanking-boon','shiver',"spiteful-weapon",'stanch','starry-vision','throes-of-ecstasy','time-jump','twist-the-skein','wind-lash','avert-evil-eye','gear-shield','hods-gift','animal-friendship']:
        return ("creature",1)
    if v1_pk in ["feather-fall-a5e"]:
        return ("creature",5)
    if v1_pk in ["word-of-recall-a5e"]:
        return ("creature",5)
    if v1_pk in ["plane-shift-a5e",'telepathic-bond-a5e']:
        return ("creature",8)
    if v1_pk in ["water-breathing-a5e","water-walk-a5e"]:
        return ("creature",10)
    if v1_pk in ["wormway-a5e"]:
        return ("creature",51)
    if v1_pk in ["battlecry-ballad-a5e"]:
        return ("creature","any number")

    # Object opt-ins.
    if v1_pk.startswith(("altered-strike","create-food-and-water","grapevine","identify","light","magic-weapon","shillelagh",'stone-shape','analyze-device','ancient-shade','animate-greater-undead','blade-of-my-brother','brimstone-infusion','doom-of-the-cracked-shield','douse-light','fire-darts','fire-under-the-tongue','freeze-potion','hoarfrost','sand-ship','scribe','vital-mark','extract-foyson','hearth-charm','imbue-spell','reset-red-portal','seal-red-portal','create-or-destroy-water','secret-chest')):
        return("object",1)
    if v1_pk in ['comprehend-wild-shape']:
        return("object",2)

    # Point
    if v1_pk.startswith(("arcane-eye","arcane-sword","darkvision","druidcraft","earth-barrier","find-the-path","floating-disk",'impending-ally','searing-sun','time-in-a-bottle','hellforging','risen-road')):
        return ("point",1)
    if v1_pk.startswith(("dancing-lights","dispel-magic","friends","misty-step","purify-food-and-drink","unseen-servant","skull-road","open-red-portal")):
        return ("point",1)

    # Area
    if v1_pk.startswith(("confusion","find-traps", "forest-army","locate-animals-or-plants",'slow','mosquito-bane','eternal-echo',"who-goes-there",'winged-spies')):
        return ("area",1)
 
    
    return (None, None)


def get_casting_time(v1_casting_time):
    for CTC in v2.enums.CASTING_TIME_CHOICES:
        if v1_casting_time.split(" ")[1] == CTC[1].lower():
            return CTC[0]
    return "action"


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

def get_range(v1_range, v1_pk):
    # 30 feet
    # Self (30-feet radius)
    trimmed_range = v1_range.split(" (")[0].lower()
    for range in v2.enums.TARGET_RANGE_CHOICES:
        if trimmed_range == range[1].lower():
            return range[0]
    
    if v1_pk in ["locate-animals-or-plants-a5e"]:
        return "5miles"

    if v1_pk in ["locate-creature-a5e"]:
        return "1000"
    if v1_pk in ["sending-a5e"]:
        return "unlimited"
    if v1_pk in ['shiver']:
        return "30"
    if v1_pk in ['circle-of-devestation']:
        return "1mile"
    if v1_pk in ['risen-road']:
        return "30"


def get_damage(desc):
    #takes dn cold damage
    #take dn damage
    #base damage

    return ("",[])

def get_shape(desc):
    
    return (None, None)