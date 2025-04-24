from django.template.defaultfilters import slugify

import json

from api_v2.models import Creature, CreatureAction, CreatureActionAttack, DamageType

def main():
    count=0
    for creature in Creature.objects.filter(document='srd'):
        for ca in creature.creatureaction_set.all():
            for at in get_attack_types(ca):
                if len(get_attack_types(ca))>1:
                    if at['ismelee']:
                        name = ca.name + " Melee attack"
                    else:
                        name = ca.name + " Ranged attack"
                else:
                    name = ca.name + " attack"
                to_hit_mod = int(ca.desc.split(":")[1].split("to hit")[0].strip())
 
                reach_val = None
                if at['ismelee']:
                    reach_desc = ca.desc.split(",")[1]
                    reach_val = reach_desc.split(" ")[2]

                range = None
                long_range = None
                if "range" in ca.desc:
                    range_full=ca.desc.split("range")[1].split(",")[0].split("ft")[0]
                    if "/" in range_full:
                        range=float(range_full.split("/")[0])
                        long_range=float(range_full.split("/")[1])
                    else:
                        range=float(range_full)
                target_creature_only = True
                if "one target" in ca.desc.split("Hit")[0]:
                    target_creature_only = False

                d = get_damage_dice(ca, at['ismelee'])

                try:
                    creature_aa = CreatureActionAttack.objects.get(key=slugify(ca.key + "_" +name))
                except CreatureActionAttack.DoesNotExist:
                    creature_aa = CreatureActionAttack(
                        key=slugify(ca.key + "_" +name),
                        name=name,
                        parent=ca,
                        attack_type=at['attack_type'],
                        to_hit_mod=to_hit_mod,
                        reach=reach_val,
                        range=range,
                        long_range=long_range,
                        target_creature_only=target_creature_only,
                        damage_die_count=d['damage_die_count'],
                        damage_die_type=d['damage_die_type'],
                        damage_bonus=d['damage_bonus'],
                        damage_type=d['damage_type'],
                        extra_damage_die_count=d['extra_damage_die_count'],
                        extra_damage_die_type=d['extra_damage_die_type'],
                        extra_damage_bonus=d['extra_damage_bonus'],
                        extra_damage_type=d['extra_damage_type']
                    )
                    count+=1

                    creature_aa.save()


    print("This would add {} caas".format(count))

def get_attack_types(ca):
    if ca.desc.startswith("Melee Weapon Attack:"):
        return [{"ismelee":True,"attack_type":"WEAPON"}]
    if ca.desc.startswith("Ranged Weapon Attack:"):
        return [{"ismelee":False,"attack_type":"WEAPON"}]

    if ca.desc.startswith("Melee Spell Attack:"):
        return [{"ismelee":True,"attack_type":"SPELL"}]
    if ca.desc.startswith("Ranged Spell Attack:"):
        return [{"ismelee":False,"attack_type":"SPELL"}]

    if ca.desc.startswith("Melee or Ranged Weapon Attack:"):
        return [{"ismelee":True,"attack_type":"WEAPON"},{"ismelee":False,"attack_type":"WEAPON"}]

    return []

def get_damage_dice(ca, ismelee):
    hit_desc = ca.desc.split("Hit:")[1].split(".")[0]
    if len(hit_desc.split("damage, or"))>1:
        for hit_desc_or in hit_desc.split("damage, or"):
            if ismelee==True and "melee" in hit_desc_or:
                d = parse_damage_statement(hit_desc_or.split(".")[0])
            if ismelee==True and "two hands" in hit_desc_or:
                d = parse_damage_statement(hit_desc_or.split(".")[0])
            if ismelee==True and "shillelagh" in hit_desc_or:
                d = parse_damage_statement(hit_desc_or.split(".")[0])
            if ismelee==True and "enlarged" in hit_desc_or:
                d = parse_damage_statement(hit_desc_or.split(".")[0])
            if ismelee==True and "Small or Medium form" in hit_desc_or:
                d = parse_damage_statement(hit_desc_or.split(".")[0])
            if ismelee==True and "half of its hit points or fewer" in hit_desc_or:
                d = parse_damage_statement(hit_desc_or.split(".")[0])
            if ismelee==False and "melee" not in hit_desc_or.split(".")[0]:
                d = parse_damage_statement(hit_desc_or)

    else:
        d = parse_damage_statement(hit_desc)

 

    return d

def parse_damage_statement(damage_statement):

    # 11 (2d6 + 4) piercing  
    # or 13 (2d8 + 4) piercing damage if used with two hands to make a melee attack."
    # 15 (2d8 + 6) piercing damage plus 27 (6d8) radiant damage.
    # 1 piercing damage, and

    damage={
        "damage_die_count": None,
        "damage_die_type": None,
        "damage_bonus": None,
        "damage_type": None,
        "extra_damage_die_count": None,
        "extra_damage_die_type": None,
        "extra_damage_bonus": None,
        "extra_damage_type": None
    }
    if damage_statement.strip().startswith("The"):
        return damage
    for i, damage_block in enumerate(damage_statement.split("plus")):
        for dt in DamageType.objects.all():
            if dt.key.lower() in damage_block:
                dtype = dt.key
        die_count = None
        die_type = None
        if "(" in damage_block and "DC" not in damage_block:
            dn = damage_block.split(")")[0].split("(")[1].lower()
            if "d" in dn:
                if "+" in dn:
                    die_count = int(dn.split("+")[0].split("d")[0])
                    die_type = "D"+ dn.split("+")[0].split("d")[1].strip()
                    die_bonus = int(dn.split("+")[1])
                if "-" in dn:
                    die_count = int(dn.split("-")[0].split("d")[0])
                    die_type = "D"+ dn.split("-")[0].split("d")[1].strip()
                    die_bonus = int(dn.split("-")[1])
                else:
                    die_bonus = 0
        else:
            die_bonus = int(damage_block.strip().split(" ")[0])
        if i>0: # This is extra damage
            damage['extra_damage_type'] = dt
            damage['extra_damage_die_count'] = die_count
            damage['extra_damage_die_type'] = die_type
            damage['extra_damage_die_bonus'] = die_bonus
        else:
            damage['damage_type'] = dt
            damage['damage_die_count'] = die_count
            damage['damage_die_type'] = die_type
            damage['damage_die_bonus'] = die_bonus


    return damage

if __name__ == '__main__':
    main()