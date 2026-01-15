#!/usr/bin/env python3
"""
Southlands Player's Guide Subclass/ClassFeature Converter

Converts subclass and class feature data to Open5e API v2 JSON format.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

SCRIPT_DIR = Path(__file__).parent
RAW_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = RAW_DIR / "output"
DATA_V2_DIR = RAW_DIR.parent.parent / "v2" / "kobold-press" / "spg"

DOC_KEY = "spg"


def slugify(name: str) -> str:
    """Convert a name to a slug."""
    slug = name.lower()
    slug = re.sub(r"[''']", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


# Subclass data extracted from the PDF
SUBCLASSES = [
    # Barbarian Paths
    {
        "name": "Path of the Ankole",
        "parent_class": "srd_barbarian",
        "desc": "Barbarians following the Path of the Ankole channel the incredible power of the massive ankole, adopting their shape and trampling all who stand against them.",
        "features": [
            {
                "name": "Titan's Horns",
                "desc": "Starting when you choose this path at 3rd level, when you enter your rage, you manifest a pair of spectral ankole horns. Until your rage ends, you can attack with your horns as a bonus action, dealing 1d10 force damage on a successful hit. You can't manifest your horns again until you finish a short or long rest."
            },
            {
                "name": "Protective Hide",
                "desc": "Beginning at 6th level, your skin thickens to protect you from harm. While you are raging and you suffer a critical hit, you can turn that hit into a normal hit. You negate any effects triggered by a critical hit. You can use this feature once and regain the use of it when you finish a short or long rest."
            },
            {
                "name": "Ankole Skinwalker",
                "desc": "Beginning at 10th level, you can cast polymorph on yourself to assume the shape of an ankole until your ankole form drops to 0 hit points or you use an action to resume your normal shape. You retain your Intelligence, Wisdom, and Charisma ability scores and your skill proficiencies. You can use this feature once and regain use of it when you finish a short or long rest."
            },
            {
                "name": "Thundering Tread",
                "desc": "Starting at 14th level, when you hit a creature with your Titan's Horns, you can choose to force the target to make a Strength saving throw against DC 8 + your Strength modifier + your proficiency bonus. On a failure, the creature is knocked prone. Further, you can move through the space occupied by prone creatures up to one size larger than you, though you can't end your turn in that occupied space. As you move through the prone creature's space, you can choose to deal bludgeoning damage to it equal to your Strength modifier."
            }
        ]
    },
    {
        "name": "Path of the Inner Eye",
        "parent_class": "srd_barbarian",
        "desc": "The barbarians who follow the Inner Eye elevate their rage beyond anger to glimpse premonitions of the future.",
        "features": [
            {
                "name": "Anticipatory Stance",
                "desc": "When you choose this path at 3rd level, you can't be surprised unless you are incapacitated, and attacks against you before your first turn have disadvantage. If you take damage before your first turn, you can enter a rage as a reaction, gaining resistance to bludgeoning, piercing, and slashing damage from the triggering attack."
            },
            {
                "name": "Insightful Dodge",
                "desc": "Beginning at 6th level, when you are raging, you can use your reaction to interrupt a foe's successful attack and move 5 feet. If this movement takes you beyond the range of that successful attack, the attack instead misses. Once you use this feature, you can't use it again until the next time you enter a rage."
            },
            {
                "name": "Foretelling Tactics",
                "desc": "Starting at 10th level, when you hit a creature with a weapon attack while raging, up to two creatures of your choice who can see and hear you can use a reaction to immediately move up to 15 feet and make a single melee or ranged weapon attack against that same creature. Once you use this feature, you can't use it again until you finish a short or long rest."
            },
            {
                "name": "Preemptive Parry",
                "desc": "At 14th level, if you are raging and a creature you can see within your reach hits another creature with a weapon attack, you can use your reaction to force the attacker to reroll the attack and use the lower of the two rolls. If the result is still a hit, reduce the damage dealt by your weapon damage die + your Strength modifier."
            }
        ]
    },
    {
        "name": "Path of the Souleater",
        "parent_class": "srd_barbarian",
        "desc": "Spreading from a fringe sect among Sudvall's minotaur Knights of the Horn, souleaters deliberately infect themselves with a non-contagious variant of the ravening. These barbarians consume souls to gain the power of their foes.",
        "features": [
            {
                "name": "Souleater",
                "desc": "When you choose this path at 3rd level, you carry a dormant version of the ravening disease. When you reduce a beast, giant, humanoid, or monstrosity to 0 hit points with a successful attack, you can consume a portion of the creature's soul, gaining temporary hit points equal to the creature's CR + your Constitution modifier (minimum 1). When you consume a new soul, you can replace the benefits of the previous soul. Benefits from this feature last until you finish raging."
            },
            {
                "name": "Shield of the Soul",
                "desc": "At 6th level, you can use your Souleater ability on aberrations, elementals, and fey. In addition, when consuming a soul, you can choose to gain one of the creature's damage resistances, damage immunities, or condition immunities as your own."
            },
            {
                "name": "Bonebreaker",
                "desc": "At 10th level, you can use your Souleater ability on celestials, dragons, and fiends. In addition, when consuming a soul, your weapon attacks gain bonus damage equal to the creature's highest ability modifier (your choice)."
            },
            {
                "name": "Invincible",
                "desc": "At 14th level, you instinctively absorb a consumed soul to preserve your own life. If you have consumed a soul with your Souleater ability and drop to 0 hit points, the benefits from Souleater end and you immediately regain hit points equal to the soul's CR + your Constitution modifier."
            }
        ]
    },
    # Bardic Colleges
    {
        "name": "College of the Cat",
        "parent_class": "srd_bard",
        "desc": "Scholars and spies, heroes and hunters: whether wooing an admirer in the bright sunlight or stalking prey under the gentle rays of the moon, bards of the College of the Cat excel at diverse skills and exhibit contrary tendencies, not unlike their ineffable mistress, the goddess Bastet.",
        "features": [
            {
                "name": "Bonus Proficiencies",
                "desc": "When you join the College of the Cat at 3rd level, you gain proficiency with the Stealth and Deception skills and with thieves' tools."
            },
            {
                "name": "Inspired Pounce",
                "desc": "Also at 3rd level, you can stalk unsuspecting foes engaged in combat with your allies. When a creature you can see applies one of your Bardic Inspiration dice to a weapon attack roll, you can use your reaction to move up to half your speed and make one melee weapon attack against that enemy. You gain a bonus on your attack roll equal to the result of the spent inspiration die."
            },
            {
                "name": "My Claws Are Sharp",
                "desc": "Beginning at 6th level, when you take the Attack action, you can attack twice instead of once. When you engage in two-weapon fighting, you can use a claw attack in place of a light weapon, and you can also give a Bardic Inspiration die to a friendly creature as part of that bonus action."
            },
            {
                "name": "Catlike Tread",
                "desc": "Starting at 14th level, when you give a creature a Bardic Inspiration die, it gains advantage on Dexterity (Stealth) checks until it uses its Bardic Inspiration die. When you have no remaining Bardic Inspiration dice, you gain advantage on Dexterity (Stealth) checks that you make."
            }
        ]
    },
    {
        "name": "College of the Sky",
        "parent_class": "srd_bard",
        "desc": "The aeromancers of the sky-city of Aerdvall use their magic to keep the city afloat. Bards of the College of the Sky are proficient with the magic of the element of air, acting as the face of the city's power.",
        "features": [
            {
                "name": "Bonus Proficiencies",
                "desc": "When you join the College of the Sky at 3rd level, you gain proficiency with one of the following skills of your choice: Arcana, Nature, and Persuasion. In addition, levitate, gust of wind, and fly are considered bard spells for you."
            },
            {
                "name": "Gusting Inspiration",
                "desc": "Also at 3rd level, your study of aeromancy allows you to affect the movement and position of your allies on the battlefield. As a bonus action, you can control the winds to affect a creature that you can see and that has one of your Bardic Inspiration dice. You can either move the creature 10 feet along the ground or stand the creature up from prone."
            },
            {
                "name": "Swirling Breeze",
                "desc": "Starting at 6th level, you can use the power of the wind to keep attackers away from you. When a creature moves adjacent to you, you can use a reaction to summon a windstorm. The triggering creature must succeed on a Strength (Athletics) check against your spell DC. On a failed check, the creature is pushed back 10 feet and can't move closer to you until the start of its next turn. You can use this feature a number of times equal to your Charisma modifier."
            },
            {
                "name": "Crushing Wind",
                "desc": "At 14th level, you have mastered the powerful and dark art of driving the air from the lungs of your foes. As an action, choose one creature that is Large or smaller within 30 feet of you. The target must succeed on a Constitution saving throw against your spell DC. On a failure, the target takes 6d10 force damage and is incapacitated. You can maintain the effect each turn using your action. Once you use this feature, you can't use it again until you finish a long rest."
            }
        ]
    },
    # Cleric Domains
    {
        "name": "Cat Domain",
        "parent_class": "srd_cleric",
        "desc": "You embody the grace, strength, and resilience of felines. Eventually, you gain the ability to take the form of a lion or a tiger.",
        "features": [
            {
                "name": "Cat Domain Spells",
                "desc": "You gain domain spells at the cleric levels listed. 1st: find familiar (feline only), speak with animals. 3rd: animal messenger, pass without trace. 5th: bestow curse, nondetection. 7th: dimension door, locate creature. 9th: commune with nature, mislead."
            },
            {
                "name": "Silent Claws",
                "desc": "When you choose this domain at 1st level, you learn the true strike cantrip and you gain proficiency in Acrobatics and Stealth."
            },
            {
                "name": "Channel Divinity: Feline Finesse",
                "desc": "At 2nd level, you can use your Channel Divinity to add a +10 bonus to a single Dexterity ability check or Dexterity-based skill check made by you or someone you designate within 30 feet. You make this choice after you see the roll but before the GM says whether the check succeeds or fails."
            },
            {
                "name": "Eyes of the Cat",
                "desc": "Beginning at 6th level, you gain darkvision out to a range of 60 feet. If you already have darkvision, the range becomes 90 feet."
            },
            {
                "name": "Divine Strike",
                "desc": "At 8th level, you gain the ability to infuse your weapon strikes with divine energy. Once on each of your turns when you hit a creature with a weapon attack, you can cause the attack to deal an extra 1d8 damage of the same type dealt by the weapon. When you reach 14th level, the extra damage increases to 2d8."
            },
            {
                "name": "Emissary of the Cat",
                "desc": "At 17th level, you become a natural lycanthrope. You use the statistics of a weretiger, though your form can be that of a werelion, werepanther, wereleopard, or other large cat. Your alignment doesn't change as a result of this lycanthropy, and you can't spread the disease of lycanthropy."
            }
        ]
    },
    # Ranger Archetypes
    {
        "name": "Wasteland Strider",
        "parent_class": "srd_ranger",
        "desc": "Wasteland Striders are rangers who have adapted to survive in the harshest desert environments, becoming one with the endless sands.",
        "features": [
            {
                "name": "Desert Magic",
                "desc": "At 3rd level, you learn additional spells when you reach certain levels in this class. These spells count as ranger spells for you and don't count against the number of ranger spells you know. 3rd: create or destroy water, fog cloud. 5th: blur, dust devil. 9th: wind wall, meld into stone. 13th: hallucinatory terrain, fire shield. 17th: control winds, wall of stone."
            },
            {
                "name": "Sand Walker",
                "desc": "Also at 3rd level, you can move across difficult terrain made of sand, dust, or rocky desert terrain without expending extra movement. You also have advantage on saving throws against exhaustion caused by extreme heat."
            },
            {
                "name": "Mirage Step",
                "desc": "At 7th level, as a bonus action, you can become invisible until the start of your next turn. This invisibility ends early if you attack or cast a spell. You can use this feature a number of times equal to your Wisdom modifier (minimum of once), and you regain all expended uses when you finish a long rest."
            },
            {
                "name": "Desert's Fury",
                "desc": "At 11th level, when you hit a creature with a weapon attack, you can choose to deal an additional 2d8 fire damage. You can use this feature a number of times equal to your Wisdom modifier, regaining all uses after a long rest."
            },
            {
                "name": "One with the Sands",
                "desc": "At 15th level, you gain resistance to fire damage. Additionally, you can cast meld into stone at will, but only to meld into sand or desert rock."
            }
        ]
    },
    # Warlock Patrons
    {
        "name": "The Great Serpent",
        "parent_class": "srd_warlock",
        "desc": "Your patron is an ancient serpentine entity of immense power, perhaps a great world serpent or primordial snake deity. Such beings are found throughout the Southlands mythology.",
        "features": [
            {
                "name": "Expanded Spell List",
                "desc": "The Great Serpent lets you choose from an expanded list of spells when you learn a warlock spell. 1st: charm person, false life. 2nd: suggestion, blindness/deafness. 3rd: fear, stinking cloud. 4th: dominate beast, freedom of movement. 5th: dominate person, hold monster."
            },
            {
                "name": "Serpent's Blessing",
                "desc": "Starting at 1st level, you gain proficiency in the Deception and Persuasion skills. Your patron also teaches you to speak, read, and write Draconic."
            },
            {
                "name": "Coils of the Serpent",
                "desc": "At 6th level, when a creature misses you with a melee attack, you can use your reaction to grapple that creature. While grappling a creature this way, you can use a bonus action on each of your turns to deal 2d6 bludgeoning damage to the grappled creature."
            },
            {
                "name": "Serpent Form",
                "desc": "At 10th level, you can cast polymorph on yourself to assume the form of a giant constrictor snake or giant poisonous snake. You can do this once without expending a spell slot, regaining the ability after a long rest."
            },
            {
                "name": "Avatar of the Serpent",
                "desc": "At 14th level, you can transform into a massive serpentine form. As an action, you grow to Large size, gain 50 temporary hit points, and your melee weapon attacks deal an additional 2d6 poison damage. This transformation lasts for 1 minute. Once you use this feature, you can't use it again until you finish a long rest."
            }
        ]
    }
]


def convert_subclasses() -> tuple[list, list]:
    """Convert subclasses and features to Open5e format."""
    subclass_list = []
    feature_list = []

    for sub_data in SUBCLASSES:
        name = sub_data["name"]
        slug = slugify(name)
        pk = f"{DOC_KEY}_{slug}"

        # Create subclass entry (as CharacterClass with subclass_of)
        subclass = {
            "model": "api_v2.characterclass",
            "pk": pk,
            "fields": {
                "name": name,
                "desc": sub_data["desc"],
                "document": DOC_KEY,
                "subclass_of": sub_data["parent_class"],
                "hit_dice": None,
                "caster_type": None,
                "primary_abilities": [],
                "saving_throws": []
            }
        }
        subclass_list.append(subclass)

        # Create feature entries
        for feature in sub_data.get("features", []):
            feature_slug = slugify(feature["name"])
            feature_pk = f"{pk}_{feature_slug}"

            feature_list.append({
                "model": "api_v2.classfeature",
                "pk": feature_pk,
                "fields": {
                    "name": feature["name"],
                    "desc": feature["desc"],
                    "document": DOC_KEY,
                    "parent": pk
                }
            })

    return subclass_list, feature_list


def main():
    print("=" * 60)
    print("Southlands Player's Guide Subclass Converter")
    print("=" * 60)

    subclass_list, feature_list = convert_subclasses()

    print(f"\nConverted {len(subclass_list)} subclasses with {len(feature_list)} features")

    # Save subclasses
    subclass_path = DATA_V2_DIR / "CharacterClass.json"
    with open(subclass_path, "w", encoding="utf-8") as f:
        json.dump(subclass_list, f, indent=2, ensure_ascii=False)
    print(f"Saved subclasses to {subclass_path}")

    # Save features
    feature_path = DATA_V2_DIR / "ClassFeature.json"
    with open(feature_path, "w", encoding="utf-8") as f:
        json.dump(feature_list, f, indent=2, ensure_ascii=False)
    print(f"Saved class features to {feature_path}")

    print("\n" + "=" * 60)
    print("Conversion complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
