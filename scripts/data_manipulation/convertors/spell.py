from api import models as v1
from api_v2 import models as v2


# Run this by:
#$  python manage.py shell -c 'from scripts.data_manipulation.spell import casting_option_generate; casting_option_generate()'
def casting_option_generate():
    success_spell_count=0
    success_option_count=0
    for v2_spell in v2.Spell.objects.all():
        success_option_count += generate_casting_options(v2_spell)
        success_spell_count += 1


    print("Generated {} options for {} spells.".format(success_option_count, success_spell_count))

# Run this by:
#$ python manage.py shell -c 'from scripts.data_manipulation.convertors.spell import fixup_spell_casting_time; fixup_spell_casting_time()'
def fixup_spell_casting_time():
  success_count = 0
  fail_list=[]
  failed=False
      
  try:
    for v2_spell in v2.Spell.objects.all():
      [doc, slug] = v2_spell.key.split("_")
      if doc == "a5e-ag":
          slug = slug + "-a5e"

      v1_spell = v1.Spell.objects.get(pk=slug)
      [v2_spell.casting_time, v2_spell.reaction_condition] = get_casting_time(v1_spell.casting_time)
      v2_spell.save()


  except Exception as e:
    print(e)
    exit(1)
      

# Run this by:
#$  python manage.py shell -c 'from scripts.data_manipulation.spell import spellmigrate; spellmigrate()'
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

def casting_option_cleanup():
    for v2_spell in v2.Spell.objects.all():
        has_ritual_co = False
        for co in v2_spell.casting_options().all():
            if co.type.find("slot")>=0:
                if int(co.type.split("_")[2])==v2_spell.level:
                    print("Deleting CO {} for {}".format(co.type, v2_spell.pk))
                    co.delete()
            if co.type=="ritual":
                has_ritual_co = True
        if v2_spell.ritual != has_ritual_co:
            # This spell needs a ritual
            print("Adding ritual CO for {}".format(v2_spell.pk))

def durationer():
    durations=[]
    for v2_spell in v2.Spell.objects.all():
        v1_spell = v1.Spell.objects.get(pk=v2_spell.pk)
        if v1_spell.requires_concentration:
            duration = "".join(v2_spell.duration.split("up to "))
            v2_spell.concentration=True
        else:
            duration = v2_spell.duration

        #v2_spell.duration=duration
        v2_spell.save()
        print(v2_spell.key, v2_spell.duration)

def cost_refactor():
    
    for v2_spell in v2.Spell.objects.all():
        amount=None
        consumed = False
        v1_spell=v1.Spell.objects.get(pk=v2_spell.pk)
        if len(v1_spell.material.split("worth at least"))>1:
            amount=v1_spell.material.split("worth at least")[1].split("gp")[0].replace(",","")
            consumed = v1_spell.material.find("consume")>0
            print(amount, consumed)
        v2_spell.material_cost = amount
        v2_spell.material_consumed = consumed
        v2_spell.save()

    #print("Generated {} options for {} spells.".format(success_option_count, success_spell_count))

def range_setter():
    for v2_spell in v2.Spell.objects.all():
        for rc in v2.enums.SPELL_TARGET_RANGE_CHOICES:
            if v2_spell.range == rc[0]:
                print("Changing from {} to {}".format(v2_spell.range,rc[1]))
                v2_spell.range=rc[1]
                v2_spell.save()

def target_counter():
    for v2_spell in v2.Spell.objects.all():
        if targets_scale(v2_spell):
            every_slot = False
            every_other_slot = False
            if v2_spell.higher_level.find("for each slot level above")>0: 
                every_slot=True

            if v2_spell.higher_level.find("for every two slot levels above")>0:
                every_other_slot = True

            slope = 1
            if every_slot == True: slope = 1
            if every_other_slot == True: slope = 2

            for co in v2_spell.casting_options().all():
                if co.type=="default":
                    continue
                if co.type=="ritual":
                    continue
                if co.type.startswith("slot_level"):
                    slot_level = int(co.type.split("_")[2])
                    multiplier = (slot_level - v2_spell.level)//slope
                    final_targets = v2_spell.target_count + multiplier
                    print("At level {} {} should have {} targets.".format(slot_level,v2_spell.pk,final_targets))

                    co.target_count = final_targets
                    co.save()


def range_scaled():
    spell_count = 0
    for v2_spell in v2.Spell.objects.all():
        if v2_spell.higher_level is not None:
            if v2_spell.higher_level.find(" duration")>=0:
                spell_count+=1
                print("https://open5e.com/spells/{} may scale with duration.".format(v2_spell.key))
                #print(v2_spell.key, v2_spell.higher_level)


    print("found {} spells that might scale with range".format(spell_count))

def map1to2(v1_spell):
    # Get documents, and map them.

    # Select target type.

    # Fit Action into the correct size.
    #print(v1_spell.higher_level)

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
        attack_roll=get_attack_roll(v1_spell.desc),
        damage_roll=get_damage(v1_spell.desc)[0],
        damage_types=get_damage(v1_spell.desc)[1],
        duration=v1_spell.duration.lower(),
        shape_type=get_shape(v1_spell.desc)[0],
        shape_magnitude=get_shape(v1_spell.desc)[1],
        school=v1_spell.school.lower(),
        higher_level=v1_spell.higher_level
    ).save()

def doc2to1(v2_doc):
    if v2_doc.key == "a5e-ag":
        return "a5e"
    else:
        return None

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
    for CTC in v2.enums.SPELL_CASTING_TIME_CHOICES:
        if "," in v1_casting_time:
            [cast_time, reaction_condition] = v1_casting_time.split(", ", 1)
        else:
            [cast_time, reaction_condition] = [v1_casting_time, None]
        cast_time = cast_time.lower()
        if cast_time.split(" ")[1] == CTC[1].lower() or cast_time == CTC[1].lower():
            return [CTC[0], reaction_condition]

    if v1_casting_time == "10 minutes plus 1 hour of attunement":
        return ["10minutes", None]

    raise ValueError("Could not process" + v1_casting_time + " into a cast_time enum") 


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
    for range in v2.enums.SPELL_TARGET_RANGE_CHOICES:
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
    #takes 2d8 cold damage
    #takes 8d6 fire damage
    damage_roll_list=[]
    damage_types = []
    half_damage = False
    for sentence in desc.split("."):

        if sentence.find("takes")>0:
            if sentence.find("damage")>0:
                dmg=sentence.split("takes")[1].split("damage")[0]
                if dmg.strip() == "": # Exclude just the phrase "takes damage"
                    continue
                if dmg.find("any")>0: # Exclude the phrase "takes any damage"
                    continue
                if dmg.find("no")>0: # Exclude the phrase "takes no damage"
                    continue
                if dmg.find("the")>0: # Exclude the phrase "takes the damage"
                    continue
                if dmg.find("half")>0: # Note that there's a mention of "takes half damage" in the spell.
                    half_damage = True # Not used.
                    continue
                
                for damage_type in v2.enums.DAMAGE_TYPES:
                    if dmg.lower().find(damage_type[0].lower())>0:
                        if len(dmg.strip().split(" "))==1:
                            # Only the damage type, exclude
                            continue
                        damage_types.append(damage_type[0].lower())
                        if len(dmg.strip().split(" "))>1:
                            #print("Found: dn={}".format(dn))
                            for word in dmg.strip().split(" "):
                                isnumber=False
                                if word.strip()=="+":
                                    damage_roll_list.append(word)
                                try: 
                                    num=int(word.strip())
                                    isnumber=True
                                    damage_roll_list.append(word.strip())
                                except: 
                                    pass
                                if len(word.strip().split("d"))==2:
                                    dn=True
                                    for n in word.strip().split("d"):
                                        try: 
                                            int(n.strip())
                                        except: 
                                            dn=False
                                    if dn:
                                        damage_roll_list.append(word.strip())
                break #Adding this in so that only the first sentence which has damage gets added into the list.


    # Adding some deduping logic here:
    if damage_roll_list!=[]:
        if damage_roll_list.count(damage_roll_list[0])==len(damage_types):
            if "+" in damage_roll_list:
                pass

            else:
                damage_roll_list=[damage_roll_list[0]]

    damage_roll = "".join(damage_roll_list)

    #print("dmg: {},{}".format(damage_roll,damage_types))

    return (damage_roll,damage_types)


def get_attack_roll(desc):
    keyphrases = ["Make a ranged spell attack", "Make a melee spell attack"]
    for keyphrase in keyphrases:
        keyphrase = keyphrase.lower()
        desc = desc.lower()
        if desc.find(keyphrase)>0:
            return True
    return False


def get_shape(desc):
    shape=None
    magnitude=None

    for sentence_unclean in desc.split("."):
        sentence = sentence_unclean.strip().lower()

        for shape_choice in v2.enums.SPELL_EFFECT_SHAPE_CHOICES:
            s = " "+shape_choice[0].lower() # Prepending a space because it's always used in a sentence.
            if sentence.find(s)>0:
                if sentence.find ("foot-radius")>0: # Good for sphere, and cylinder
                    for word in sentence.split(" "):
                        if word.endswith("foot-radius"):
                            try:
                                magnitude = int(word.split("-")[0])
                                shape=shape_choice[0]
                            except:
            
                                continue
                
                if sentence.find("-foot")>0: # Good for cube:
                    for word in sentence.split(" "):
                        if word.endswith("-foot"):
                            try:
                                magnitude = int(word.split("-")[0])
                                shape=shape_choice[0]
                            except:
                                continue
                        


        if magnitude is not None: # Tend towards returning the first good result (in a sentence) rather than the last.
            #print("mag:{} shape:{}".format(magnitude,shape))
            return (shape, magnitude)

    return (shape, magnitude)


def generate_casting_options(v2_spell):
    #options_count=0
    ## Create Default option.
    v2.CastingOption(
        spell=v2_spell,
        type='default'
    ).save()
    options_count+=1
    
    # Generate the ritual version.
    if v2_spell.ritual:
        v2.CastingOption(
            spell=v2_spell,
            type='ritual'
        ).save()
        options_count+=1

    if v2_spell.higher_level!="":
        #Options exist at higher levels (player OR slot)
        if v2_spell.level==0:
            # We need to generate some player-leveled cantrips.
            for player_level in range(1,21): #end number is not included
                cantrip_option = get_cantrip_options(v2_spell, player_level)
                cantrip_option.check()
                options_count +=1
        if v2_spell.level>0:
            for slot_level in range(v2_spell.level, 10): #end number is not included
                spell_option = get_spell_options(v2_spell, slot_level)
                spell_option.save()
                options_count+=1
            # We need to generate some slot-leveled options.

    return options_count


def get_cantrip_options(v2_spell,player_level):
    # Unique Options:

    if v2_spell.pk in ["altered-strike-a5e",'pestilence-a5e','ale-dritch-blast','biting-arrow','clockwork-bolt','shadow-bite','starburst']:
        # SKIP THESE, need to be hand-converted. They are damage scaling, but don't match the formatting below.
        option = v2.CastingOption(
            spell=v2_spell,
            type="player_level_{}".format(player_level),
        )
        return option

    if v2_spell.pk in ['animated-scroll','blood-tide','shiver','obfuscate-object']:
    # duration or other-based, needs to be hand-converted.
        option = v2.CastingOption(
            spell=v2_spell,
            type="player_level_{}".format(player_level),
        )
        return option

    damage_roll_changes = False

    higher_levels_text_implies_damage = False
    if v2_spell.higher_level.startswith("This spell's damage increases"): 
        higher_levels_text_implies_damage = True
    if v2_spell.higher_level.startswith("This spell’s damage increases"): 
        higher_levels_text_implies_damage = True
    if v2_spell.higher_level.startswith("The spell's damage increases by"):
        higher_levels_text_implies_damage = True
    if v2_spell.higher_level.startswith("The spell’s damage increases by"):
        higher_levels_text_implies_damage = True
    if v2_spell.higher_level.startswith("The damage increases when you reach higher"):
        higher_levels_text_implies_damage = True

    if higher_levels_text_implies_damage:

        damage_roll_changes = True
        if player_level < 5:
            damage_roll=v2_spell.damage_roll
        if player_level >= 5 and player_level < 11 :
            for phrase in v2_spell.higher_level.split(','):
                if phrase.find("5th level")>0:
                    damage_roll = phrase.split("5th level")[1].strip().split("(")[1].split(")")[0]
        if player_level >=11 and player_level < 17:
            for phrase in v2_spell.higher_level.split(','): 
                if phrase.find("11th level")>0:
                    damage_roll = phrase.split("11th level")[1].strip().split("(")[1].split(")")[0]
        if player_level >=17:
            for phrase in v2_spell.higher_level.split(','):
                if phrase.find("17th level")>0:
                    damage_roll = phrase.split("17th level")[1].strip().split("(")[1].split(")")[0]
        option = v2.CastingOption(
            spell=v2_spell,
            type="player_level_{}".format(player_level),
            damage_roll=damage_roll
        )
        return option

    targets_scale=False
    if v2_spell.pk.startswith("eldritch-blast"):
        targets_scale=True
        option = v2.CastingOption(
            spell=v2_spell,
            type="player_level_{}".format(player_level),
            target_count=2
        )
        return option
    

    if v2_spell.higher_level.startswith("The duration of this spell increases when you reach"):
        option = v2.CastingOption(
            spell=v2_spell,
            type="player_level_{}".format(player_level),
            duration="10minutes" # Hardcoded, need to fix.
        )
        return option
    
    print(v2_spell.pk)

    return None


def get_spell_options(v2_spell,slot_level):
    
    option = v2.CastingOption(
        spell=v2_spell,
        type="slot_level_{}".format(slot_level)
        )

    erroroneous_higher_level="When you cast this spell using a spell slot of 5th level or higher, the damage increases by your choice of 1d6 cold damage or 1d6 piercing damage"
    if v2_spell.higher_level.startswith(erroroneous_higher_level):
        #error, should be fixed soon.
            return option

    skipped_from_damage_parsing = ['muted-foe','repulsing-wall','blade-barrier-a5e','blight-a5e','call-lightning-a5e','circle-of-death-a5e','cobras-spit-a5e','finger-of-death-a5e','fire-storm-a5e','flame-blade-a5e','flaming-sphere-a5e','freezing-sphere-a5e',"glyph-of-warding-a5e",'guiding-bolt-a5e',"glyph-of-warding-a5e",'ice-storm-a5e','inescapable-malady-a5e','inflict-wounds-a5e','insect-plague-a5e','moonbeam-a5e','shatter-a5e','spiritual-weapon-a5e','thunderwave-a5e','vampiric-touch-a5e','venomous-succor-a5e','wall-of-fire-a5e','whirlwind-kick-a5e','wind-wall-a5e','booster-shot','dragon-breath','elemental-horns','essence-instability','fire-darts','frozen-razors','freezing-fog','flame-wave','ectoplasm','earworm-melody','destructive-resonance','death-gods-touch','consult-the-storm','clash-of-glaciers','chains-of-torment','catapult','boiling-oil','bloodshot','blade-of-wrath','acid-rain','abhorrent-apparition']
    skipped_from_damage_parsing += ['wall-of-flesh-a5e','legion-of-rabid-squirrels','life-drain','nether-weapon','poisoned-volley','reaver-spirit','reverberate','steam-blast','branding-smite','delayed-blast-fireball','phantasmal-killer','spiritual-weapon']
    #skipped=[]
    if v2_spell.pk in skipped_from_damage_parsing:

    # SKIP THESE, need to be hand-converted. They don't match formatting.

        return option

    
    every_slot = False
    every_other_slot = False
    if v2_spell.higher_level.find("for each slot level above")>0: 
        every_slot=True

    if v2_spell.higher_level.find("for every two slot levels above")>0:
        every_other_slot = True

    if v2_spell.higher_level.find("duration")>0:
        if v2_spell.higher_level.find("spell's duration")<0:
            # These appear to be the spells who's duration is impacted at higher levels.
            option = v2.CastingOption(
                spell=v2_spell,
                type="slot_level_{}".format(slot_level),
                duration="0"
                )

    if v2_spell.higher_level.find("range")>0:
        if v2_spell.higher_level.find("ranged")<0:
            # These appear to be the spells whose range scales.
            option = v2.CastingOption(
                spell=v2_spell,
                type="slot_level_{}".format(slot_level),
                range="0"
                )

    # get every or every-other slot
    higher_levels_text_implies_damage = False
    if v2_spell.higher_level.find("damage increases by")>0: 
        higher_levels_text_implies_damage = True
    if v2_spell.higher_level.find("damage (your choice) increases")>0:
        higher_levels_text_implies_damage = True

    if higher_levels_text_implies_damage:
        
        increase = v2_spell.higher_level.split("increases by")[1].split(" ")[1].strip()

        # dice notation addition time
        damage_roll = v2_spell.damage_roll
        
        slope = 1
        if every_slot == True: slope = 1
        if every_other_slot == True: slope = 2

        multiplier = (slot_level - v2_spell.level)//slope
        additional_dice_number = (int(increase.split('d')[0])*multiplier)
        
        #("10d6+40")
        final_damage = (int(damage_roll.split('d')[0])+additional_dice_number,int(damage_roll.split('d')[1].split('+')[0]))
        
        final_damage_str = str(final_damage[0]) + "d" + str(final_damage[1])
        if "+" in damage_roll:
            final_damage_str += "+"+damage_roll.split("+")[1]
        #if v2_spell.pk == 'disintegrate':
        #    print("Name: {} Slot Level:{} Damage Roll:{} Final Roll:{}".format(v2_spell.pk, slot_level, damage_roll, final_damage_str))
        
        option = v2.CastingOption(
            spell=v2_spell,
            type="slot_level_{}".format(slot_level),
            damage_roll = final_damage_str
        )

        

    return option

def delete_casting_options():
    for co in v2.CastingOption.objects.all():
        co.delete()



def targets_scale(v2_spell):
    targets_scale=False
    if v2_spell.pk in ['magic-missile', 'scorching-ray']:
        targets_scale=True
    if v2_spell.higher_level.find("target one additional")>0:
        targets_scale=True
    if v2_spell.higher_level.find("Target one additional")>=0:
        targets_scale=True
    if v2_spell.higher_level.find("targets one additional")>0:
        targets_scale=True
    if v2_spell.higher_level.find("create one additional")>0:
        targets_scale=True
    if v2_spell.higher_level.find("target up to one additional")>0:
        targets_scale=True
    if v2_spell.higher_level.find("affect one additional")>0:
        targets_scale=True
    return targets_scale