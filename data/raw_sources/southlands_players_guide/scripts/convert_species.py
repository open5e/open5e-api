#!/usr/bin/env python3
"""
Southlands Player's Guide Species (Race) Converter

Converts race/species data to Open5e API v2 JSON format.
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


# Species data extracted from the PDF
SPECIES = [
    # Base races (subspecies_of: None)
    {
        "name": "Catfolk",
        "desc": "Catfolk are a social and active people of natural grace and obsessive curiosity, resembling bipedal, feline humanoids with tails, cat-like ears, and fur. They are equally comfortable wandering in far-off regions, wallowing in the heart of the largest cities, or delving into the lair of forgotten horrors.",
        "subspecies_of": None,
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Dexterity score increases by 2."},
            {"name": "Age", "desc": "Catfolk mature at the same rate as humans and can live just past a century."},
            {"name": "Alignment", "desc": "Catfolk tend toward two extremes. Some are free-spirited and chaotic, letting impulse and fancy guide their decisions. Others are devoted to duty and personal honor."},
            {"name": "Size", "desc": "Catfolk have a similar stature to humans but are generally leaner and more muscular. Your size is Medium."},
            {"name": "Speed", "desc": "Your base walking speed is 30 feet."},
            {"name": "Darkvision", "desc": "You have a cat's keen senses, especially in the dark. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray."},
            {"name": "Cat's Claws", "desc": "You have claws that you can use as natural weapons to make unarmed strikes. If you hit with them, you deal slashing damage equal to 1d4 + your Strength modifier, instead of the bludgeoning damage normal for an unarmed strike."},
            {"name": "Hunter's Senses", "desc": "You have proficiency in the Perception and Stealth skills."},
            {"name": "Languages", "desc": "You can speak, read, and write Common and either Nurian, Nkosi or the Southern Trade Tongue."},
        ]
    },
    {
        "name": "Basteti",
        "desc": "Basteti are the adored children of Bastet the cat goddess. These mischievous catfolk turn curiosity into a cultural obsession, adoring new experiences, collecting interesting artifacts, and meeting unique strangers.",
        "subspecies_of": "spg_catfolk",
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Charisma score increases by 1."},
            {"name": "Bastet's Blessing", "desc": "The gift of the goddess allows you to communicate in a limited manner with non-humanoid feline beasts. They can understand the meaning of your words, though you have no special ability to understand them in turn. You have advantage on all Charisma checks you make to influence them."},
            {"name": "Climber", "desc": "Your reflexes and claws allow you to scale vertical surfaces with a burst of speed. When you move at least 10 feet horizontally first, you can use the rest of your movement to traverse vertical surfaces."},
            {"name": "Stalker's Reflex", "desc": "You have advantage on Dexterity checks for initiative."},
        ]
    },
    {
        "name": "Nkosi",
        "desc": "The Nkosi are the chosen people of Gamka the Returned Titan and serve as the protectors of Omphaya. Nkosi consider their ability to change shape to be a divine gift and distrust lycanthropes.",
        "subspecies_of": "spg_catfolk",
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Strength score increases by 1."},
            {"name": "Form of the Lion", "desc": "As an action, you can assume a leonine form. While in this form, your statistics remain the same, except you move as a quadruped instead of a biped, you can't speak or cast spells, and your speed increases by 10 feet. Additionally, you have advantage on Wisdom (Perception) checks that rely on smell, and you gain a bite attack that deals 1d6 + Strength modifier piercing damage. You can revert to your normal form as an action."},
        ]
    },
    {
        "name": "Gnoll",
        "desc": "The average gnoll views work and self-sufficiency with distaste. Gnolls who possess the will to face danger make excellent adventurers.",
        "subspecies_of": None,
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Strength score increases by 2."},
            {"name": "Age", "desc": "Gnolls reach adulthood at age 12, and they live short and brutal lives. The rare examples that die of old age experience only around 70 summers."},
            {"name": "Alignment", "desc": "As a product of a culture that values laziness, selfishness, and dominance, most gnolls are evil. An unpredictable existence usually leads to a chaotic view of the world."},
            {"name": "Size", "desc": "Gnoll females are taller and more powerfully built than their male counterparts. The former range from 7 to 8 feet and usually weigh more than 250 pounds. Your size is Medium."},
            {"name": "Speed", "desc": "Your base walking speed is 30 feet."},
            {"name": "Darkvision", "desc": "You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You cannot discern color in darkness, only shades of gray."},
            {"name": "Scent", "desc": "You have advantage on Wisdom (Perception) checks that rely on smell."},
            {"name": "Bully", "desc": "You have disadvantage on saving throws against being frightened. However, whenever you make a Charisma (Intimidation) check involving obviously smaller or weaker targets, you are considered proficient in the Intimidation skill and add double your proficiency bonus to the check."},
            {"name": "Live to Fight Another Day", "desc": "When you take the Disengage action, your base walking speed increases by 10 feet until the end of your turn."},
            {"name": "Gnoll Weapon Training", "desc": "You have proficiency with the spear, shortbow, longbow, light crossbow, and heavy crossbow."},
            {"name": "Languages", "desc": "You can speak, read, and write Southern and Gnollish."},
        ]
    },
    {
        "name": "Civilized Gnoll",
        "desc": "As a civilized gnoll, you are well-fed and enjoy the comforts that your more rural cousins can only dream of. You were valued as a mercenary, a temple guard, or simply a thug.",
        "subspecies_of": "spg_gnoll",
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Constitution score increases by 1."},
            {"name": "Obsequious", "desc": "Whenever you make a Charisma (Persuasion) check for dealing with obviously bigger or more powerful targets, you are considered proficient in the Persuasion skill and add double your proficiency bonus to the check."},
        ]
    },
    {
        "name": "Savage Gnoll",
        "desc": "As a savage gnoll, you are in touch with your animal side and understand the ways of nature. Your tribe has been raiding the desert or the plains since generations ago.",
        "subspecies_of": "spg_gnoll",
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Wisdom score increases by 1."},
            {"name": "Scavenge", "desc": "Whenever you make a Wisdom (Survival) check for gathering food or locating water, you are considered proficient in the Survival skill and add double your proficiency bonus to the check."},
        ]
    },
    {
        "name": "Desert Gnoll",
        "desc": "As a desert gnoll, you use the terrain to your advantage. You can endure heat and dehydration far beyond the limits of most humanoids, making you a superlative hunter, raider, or caravan guard.",
        "subspecies_of": "spg_gnoll",
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Charisma score increases by 1."},
            {"name": "Heat Tolerance", "desc": "You have resistance to fire damage. You can go three times as long without water as most other humanoids."},
        ]
    },
    {
        "name": "Necropolis Gnoll",
        "desc": "As a necropolis gnoll, you spent most of your life among tombs, where the only other living creatures were members of your tribe. You're adept at avoiding traps and the powers of rot and undeath.",
        "subspecies_of": "spg_gnoll",
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Dexterity score increases by 1."},
            {"name": "Among the Dead", "desc": "You have resistance to necrotic damage."},
            {"name": "Curse Defiance", "desc": "You have advantage on saving throws against curses."},
        ]
    },
    {
        "name": "Jinnborn",
        "desc": "Native to the deepest deserts, the jinnborn claim they were the first mortals to walk the world. Descended from powerful elemental creatures called the Jinn, the jinnborn manifest gifts through their lineage that help them survive their harsh home environment.",
        "subspecies_of": None,
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Constitution score increases by 2."},
            {"name": "Age", "desc": "Jinnborn reach maturity at age 16 and can live to be over 150."},
            {"name": "Alignment", "desc": "There is no single alignment among the jinnborn that typifies them all."},
            {"name": "Size", "desc": "Jinnborn tend to be slightly shorter than humans, with stout, well-muscled builds. Your size is Medium."},
            {"name": "Speed", "desc": "Your base walking speed is 30 feet."},
            {"name": "Darkvision", "desc": "Thanks to your jinn blood, you can see in dim light within 60 feet as though it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray."},
            {"name": "Desert Dependent", "desc": "At least once each year, you must spend 8 hours meditating in a desert or other warm, arid environment to reaffirm your siraati and your connection to your tribe's patron jinn. If you refuse or are unable to meditate in this way, you lose sight of your siraati and become vulnerable to a type of damage opposed to your siraati."},
            {"name": "Negotiator", "desc": "You have proficiency in the Persuasion skill."},
            {"name": "Siraati", "desc": "All jinnborn have an affinity for mystic paths, depending on the jinn patron of their tribe. Choose one of the following siraati: air, earth, fire, or water."},
            {"name": "Languages", "desc": "You can speak, read, and write Common and one of the four elemental languages (Auran, Aquan, Ignan, or Terran). The elemental language must conform to your siraati."},
        ]
    },
    {
        "name": "Speaker Jinnborn",
        "desc": "Speaker jinnborn bear the mark of their jinni patron, and the world must stand up and take notice. They are the guides, elders, and leaders of their tribes, as well as scouts and seekers of paths.",
        "subspecies_of": "spg_jinnborn",
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Wisdom score increases by 1."},
            {"name": "Favor of the Jinn", "desc": "You can call upon your jinn patron to gain advantage on a saving throw or ability check, or to impose disadvantage on an attack roll against you. You can use this ability a number of times equal to your Wisdom modifier (minimum of 1). You regain all expended uses when you finish a long rest."},
            {"name": "Walker", "desc": "You have advantage on saving throws against being stunned and the effects of extreme environments, and on ability checks made to navigate the wilderness and avoid losing your way."},
        ]
    },
    {
        "name": "Shaper Jinnborn",
        "desc": "The Shaper jinnborn channel the elemental power of their tribe's siraati. Shapers form the majority of a tribe's warriors and protectors.",
        "subspecies_of": "spg_jinnborn",
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Strength score increases by 1."},
            {"name": "Elemental Strike", "desc": "Once on your turn when you hit with a melee attack, you can deal an additional 1d6 damage. The damage type corresponds to your siraati (lightning for air, acid for earth, fire for fire, cold for water). You can use this ability a number of times equal to your Constitution modifier (minimum of 1)."},
            {"name": "Protection of the Jinn", "desc": "You have resistance against a type of damage that corresponds to your siraati (lightning for air, acid for earth, fire for fire, cold for water)."},
        ]
    },
    {
        "name": "Minotaur",
        "desc": "The proud minotaurs of the Southlands seek to reclaim their ancestral glories from the ruins of the past. The bull-folk are imposing and powerful, with a well-earned reputation for ferocity that borders on monstrous.",
        "subspecies_of": None,
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Strength score increases by 2, and your Constitution score increases by 1."},
            {"name": "Age", "desc": "Minotaurs mature at roughly the same rate as humans but mature 3 years earlier. Childhood ends around the age of 10 and adulthood is celebrated at 15."},
            {"name": "Alignment", "desc": "Minotaurs possess a wide range of alignments. Mixing a love for personal freedom and respect for history and tradition, the majority of minotaurs fall into neutral alignments."},
            {"name": "Size", "desc": "Adult males can reach a height of 6½ to 7 feet, with females averaging 3 inches shorter. Your size is Medium."},
            {"name": "Speed", "desc": "Your base walking speed is 30 feet."},
            {"name": "Darkvision", "desc": "You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You cannot discern color in darkness, only shades of gray."},
            {"name": "Natural Attacks", "desc": "You have proficiency with your horns, which deal 1d6 piercing damage."},
            {"name": "Charge", "desc": "If you move at least 10 feet toward a target and hit it with a horn attack in the same turn, you deal an extra 1d6 piercing damage and you can shove the target as a bonus action. You can apply this extra damage once per turn."},
            {"name": "Labyrinth Sense", "desc": "You can retrace without error any path you have previously taken, with no ability check."},
            {"name": "Languages", "desc": "You can speak, read, and write Minotaur, as well as one other language of your choice."},
        ]
    },
    {
        "name": "Tosculi",
        "desc": "The tosculi are insectoid humanoids, operating under a shared consciousness. A fearsome and ruthless insectoid queen rules each hive city. Hiveless tosculi are outcasts who possess individualism and can become adventurers.",
        "subspecies_of": None,
        "traits": [
            {"name": "Ability Score Increase", "desc": "One of your physical ability scores (Strength, Dexterity, Constitution) increases by 2, and one of your mental ability scores (Intelligence, Wisdom, Charisma) increases by 2. You also take a –2 penalty to any one ability score."},
            {"name": "Age", "desc": "Tosculi reach maturity at around 13 years but have shorter lifespans than most races with few living longer than 40 years."},
            {"name": "Alignment", "desc": "The tension between tosculi and other humanoids often makes it difficult for the Hiveless to develop any true sense of altruism toward others, and many are neutral in alignment."},
            {"name": "Size", "desc": "Hiveless tosculi are no more than 4 feet tall and typically weigh less than a humanoid of the same size. Your size is Small."},
            {"name": "Speed", "desc": "Your base walking speed is 30 feet."},
            {"name": "Natural Armor", "desc": "Your Armor Class cannot be less than 11 + your Dexterity modifier no matter what armor you are wearing."},
            {"name": "Natural Attacks", "desc": "You have proficiency with your claws, which deal 1d4 slashing damage."},
            {"name": "Gliding Wings", "desc": "You take no damage from falls. You gain a fly speed of 40 feet but cannot hover. At the end of any round you fly, you must have descended at least one-quarter the distance you traveled or you fall."},
            {"name": "Stalker", "desc": "You have proficiency in the Perception skill and Stealth skill."},
            {"name": "Languages", "desc": "You can speak, read, and write Tosculi and one other language of your choice."},
        ]
    },
    {
        "name": "Heru",
        "desc": "Ravenfolk, called heru in the Southlands, are valued and honored citizens in most realms. Most worship the falcon-headed god Horus, with the vast majority residing in his temples.",
        "subspecies_of": None,
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Dexterity score increases by 2 and your Charisma score increases by 1."},
            {"name": "Age", "desc": "Heru reach adulthood at 10 years old and can live to be 110."},
            {"name": "Alignment", "desc": "Heru tend toward chaos thanks to their capriciousness and insatiable curiosity. Greed overwhelms some heru, drawing them toward evil."},
            {"name": "Size", "desc": "Heru are slighter and shorter than humans. They range from 4 feet to just shy of 6 feet tall. Your size is Medium."},
            {"name": "Speed", "desc": "Your base walking speed is 30 feet."},
            {"name": "Sudden Attack", "desc": "You have advantage on attack rolls against a surprised creature."},
            {"name": "Mimicry", "desc": "Heru can mimic any sound they've heard. Make a Charisma (Deception) check against the passive Wisdom (Insight) of any listeners. Success indicates they believe the sound you created was real."},
            {"name": "Trickster", "desc": "You have proficiency in the Deception and Stealth skills."},
            {"name": "Languages", "desc": "You can use Feather Speech (your silent language), and speak, read, and write Huginn's Speech and Southern Trade Tongue."},
        ]
    },
    {
        "name": "Lizardfolk",
        "desc": "The lizardfolk are a little-known race in the Southlands, but they have existed in Midgard for untold ages. Those lizardfolk who become adventurers form strong attachments to their companions.",
        "subspecies_of": None,
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Constitution score increases by 2."},
            {"name": "Age", "desc": "Lizardfolk reach maturity around age 10 and rarely live longer than 60 years."},
            {"name": "Alignment", "desc": "Most lizardfolk are neutral, as their emotional reactions tend to be different than warm-blooded creatures."},
            {"name": "Size", "desc": "Lizardfolk are bulkier than humans, and their colorful frills make them seem even larger. Your size is Medium."},
            {"name": "Speed", "desc": "Your base walking speed is 30 feet and you have a swimming speed of 30 feet."},
            {"name": "Natural Weapons", "desc": "Your fanged maw and sharp claws are natural weapons which you can use to make unarmed strikes. Your bite deals 1d4 + your Strength modifier piercing damage, and your claws deal 1d4 + Strength modifier slashing damage."},
            {"name": "Hold Breath", "desc": "You can hold your breath for up to 15 minutes at a time."},
            {"name": "Natural Armor", "desc": "Your skin is covered with strong scales. When you aren't wearing armor, your AC is 13 + your Dexterity modifier. You can use your natural armor to determine your AC if the armor you wear would leave you with a lower AC."},
            {"name": "Hunter's Knack", "desc": "You gain proficiency with two of the following skills of your choice: Animal Handling, Nature, Perception, Stealth, and Survival."},
            {"name": "Languages", "desc": "You can read, write and speak Southern Trade Tongue and Draconic."},
        ]
    },
    {
        "name": "Murkscale",
        "desc": "The murkscale lizardfolk dwell deep within the marshes, swamps, and fens of the world, far from the dwellings of the hapless, soft, warm-blood races.",
        "subspecies_of": "spg_lizardfolk",
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Wisdom score increases by 1."},
            {"name": "Swift Swimmers", "desc": "Your swimming speed is 40 feet."},
            {"name": "Swamp Stealth", "desc": "You have advantage on Dexterity (Stealth) checks in swamp or marsh terrain."},
        ]
    },
    {
        "name": "Velesborn",
        "desc": "Harkening from the deepest, darkest jungles, the velesborn believe they are the true children of the Great Serpent, who has blessed them with natural grace and innate toughness.",
        "subspecies_of": "spg_lizardfolk",
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Dexterity score increases by 1."},
            {"name": "Gift of Grace", "desc": "You have advantage on Dexterity (Acrobatics) checks."},
            {"name": "Gift of Vigor", "desc": "Your maximum hit points increase by 1, and an additional 1 each time you gain a level."},
        ]
    },
    {
        "name": "Ramag",
        "desc": "The enigmatic ramag thrive in the heart of a land once ruled by an empire of titans. The race's natural affinity for manipulating magic made the ramag essential to tending a vast web of magical energy.",
        "subspecies_of": None,
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Intelligence score increases by 2, and your Dexterity score increases by 1."},
            {"name": "Age", "desc": "Ramag reach maturity at 15 years and can live to 90."},
            {"name": "Size", "desc": "Despite their overlong limbs, ramag stand between 5 and 6 feet tall. Your size is Medium."},
            {"name": "Alignment", "desc": "Ramag tend toward lawfulness, since their survival depends on adhering to their laws and customs."},
            {"name": "Speed", "desc": "Your base walking speed is 30 feet."},
            {"name": "Arcane Heritage", "desc": "You can ignore class requirements when attuning to a magic item."},
            {"name": "Mystical Understanding", "desc": "You have proficiency in the Arcana skill."},
            {"name": "Spell Damping", "desc": "You have advantage on Strength and Dexterity saving throws against spells."},
            {"name": "Languages", "desc": "You can speak, read, and write Common and Giant."},
        ]
    },
    {
        "name": "Subek",
        "desc": "The kindly, scholarly subek come from a river-based culture, known for advising others and lending their physical and intellectual prowess to local projects. During flood season, however, the subek become violent and territorial.",
        "subspecies_of": None,
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Constitution score increases by 2, and you choose one of the following to increase by 1: Strength, Intelligence, or Wisdom."},
            {"name": "Age", "desc": "Subek age at roughly the same rate as humans but mature faster, reaching adulthood around the age of 10. They can live up to 300 years."},
            {"name": "Alignment", "desc": "Subek possess a wide range of alignment. The ties to the natural pattern of their river homes tend to push many subek toward lawful or neutral alignments."},
            {"name": "Size", "desc": "Adult males can reach a height of 8½ feet with females averaging 5 inches shorter. Your size is Medium."},
            {"name": "Speed", "desc": "Your base walking speed is 30 feet and your swim speed is 30 feet."},
            {"name": "Darkvision", "desc": "You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You cannot discern color in darkness, only shades of gray."},
            {"name": "Natural Weapons", "desc": "Your powerful bite and sharp claws are natural weapons that you can use to make unarmed strikes. Your bite deals 1d8 + your Strength modifier piercing damage and your claws deal 1d6 + Strength modifier slashing damage."},
            {"name": "Hold Breath", "desc": "Accustomed to your watery home, you can hold your breath for up to 15 minutes."},
            {"name": "Flood Fever", "desc": "Choose three consecutive months out of the year to reflect the flood season of your river birthplace. During this time, you lose the benefits of your Scholars trait. When a creature deals damage to you, every attack you make and harmful spell you cast must include that creature as a target. Once per turn when you hit your target with an attack, you deal an additional 1d6 damage."},
            {"name": "Scholars", "desc": "When it is not flood season, you have advantage on Intelligence (History) and Intelligence (Investigation) checks."},
            {"name": "Languages", "desc": "You can speak, read, and write Southern Trade Tongue as well as a second language of your choice."},
        ]
    },
    {
        "name": "Trollkin",
        "desc": "Descended from fey, immortal, and other monstrous races, trollkin are seldom welcome among the civilized races. As a result, most trollkin live in isolated septs or tribal settlements and subsist on hunting and raiding.",
        "subspecies_of": None,
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Constitution score increases by 2."},
            {"name": "Age", "desc": "Trollkin reach maturity by the age of 15 and live up to 60 years."},
            {"name": "Alignment", "desc": "Trollkin tend toward chaotic alignments. Their fey blood makes them crave freedom and reject law, while their monstrous origins often draw them toward evil."},
            {"name": "Size", "desc": "Trollkin are tall and lanky, ranging from 6 to 7 feet tall. Your size is Medium."},
            {"name": "Speed", "desc": "Your base walking speed is 30 feet."},
            {"name": "Darkvision", "desc": "Thanks to your fey ancestry, you have superior vision in dark and dim conditions. You can see in dim light within 60 feet of you as if it were bright light, and in darkness as if it were dim light. You can't discern color in darkness, only shades of gray."},
            {"name": "Natural Weapons", "desc": "You have fangs that you can use as natural weapons to make unarmed strikes. If you hit with them, you deal piercing damage equal to 1d4 + your Strength modifier."},
            {"name": "Regeneration", "desc": "You regain hit points equal to your Constitution modifier (minimum of 1) at the start of your turn if you have at least 1 hit point. This regeneration doesn't function if you took acid or fire damage since the start of your last turn."},
            {"name": "Thick Hide", "desc": "Your tough skin provides some protection. When you aren't wearing armor, your AC equals 12 + your Dexterity modifier."},
            {"name": "Languages", "desc": "You can speak, read, and write Southern Trade Tongue and Giant."},
        ]
    },
    {
        "name": "Southern Trollkin",
        "desc": "Southern trollkin have adapted to the harsh climates of the Southlands, from the scorching deserts to the humid jungles. They are often more integrated into local communities than their northern cousins.",
        "subspecies_of": "spg_trollkin",
        "traits": [
            {"name": "Ability Score Increase", "desc": "Your Wisdom score increases by 1."},
            {"name": "Heat Adapted", "desc": "You have resistance to fire damage and are naturally adapted to hot climates."},
            {"name": "Desert Knowledge", "desc": "You have proficiency in the Survival skill."},
        ]
    },
]


def convert_species() -> tuple[list, list]:
    """Convert species to Open5e format."""
    species_list = []
    traits_list = []

    for sp_data in SPECIES:
        name = sp_data["name"]
        slug = slugify(name)
        pk = f"{DOC_KEY}_{slug}"

        # Create species entry
        species = {
            "model": "api_v2.species",
            "pk": pk,
            "fields": {
                "name": name,
                "desc": sp_data["desc"],
                "document": DOC_KEY,
                "subspecies_of": sp_data["subspecies_of"]
            }
        }
        species_list.append(species)

        # Create trait entries
        for trait in sp_data.get("traits", []):
            trait_slug = slugify(trait["name"])
            trait_pk = f"{pk}_{trait_slug}"

            traits_list.append({
                "model": "api_v2.speciestrait",
                "pk": trait_pk,
                "fields": {
                    "name": trait["name"],
                    "desc": trait["desc"],
                    "parent": pk,
                    "type": None
                }
            })

    return species_list, traits_list


def main():
    print("=" * 60)
    print("Southlands Player's Guide Species Converter")
    print("=" * 60)

    species_list, traits_list = convert_species()

    print(f"\nConverted {len(species_list)} species with {len(traits_list)} traits")

    # Save species
    species_path = DATA_V2_DIR / "Species.json"
    with open(species_path, "w", encoding="utf-8") as f:
        json.dump(species_list, f, indent=2, ensure_ascii=False)
    print(f"Saved species to {species_path}")

    # Save traits
    trait_path = DATA_V2_DIR / "SpeciesTrait.json"
    with open(trait_path, "w", encoding="utf-8") as f:
        json.dump(traits_list, f, indent=2, ensure_ascii=False)
    print(f"Saved species traits to {trait_path}")

    print("\n" + "=" * 60)
    print("Conversion complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
