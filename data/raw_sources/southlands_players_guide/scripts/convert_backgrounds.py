#!/usr/bin/env python3
"""
Southlands Player's Guide Background Converter

Converts background data to Open5e API v2 JSON format.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

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


# Background data from the PDF
BACKGROUNDS = [
    {
        "name": "Desert Runner",
        "desc": "You grew up in one of the desert areas in the northern half of the Southlands, among the Tamasheq nomads, the jinnborn, or the gnolls. As a nomad, you are used to moving from place to place, following the caravan trails. Your upbringing makes you more than just used to desert living—you thrive there. Your tribe has lived in the desert for centuries, and you know more about desert survival than life in the towns and cities.",
        "skill_proficiencies": "Perception, Survival",
        "tool_proficiencies": "Herbalist kit",
        "languages": "One of your choice",
        "equipment": "Traveler's clothes, herbalist kit, waterskin, pouch with 10 gp",
        "feature_name": "Nomad",
        "feature_desc": "Living in the open desert has allowed your body to adapt to a range of environmental conditions. You can survive on 1 gallon of water in hot conditions (or 1/2 gallon in normal conditions) without being forced to make Constitution saving throws, and you are considered naturally adapted to hot climates. You can read the environment to predict natural weather patterns and temperatures for the next 24 hours, allowing you to cross dangerous terrain at the best times. The accuracy of your predictions is up to the GM, but they should be reliable unless affected by magic or unforeseeable events, such as distant earthquakes or volcanic eruptions.",
        "suggested_characteristics": """Those raised among the desert tribes can be the friendliest of humanoids—knowing allies are better than enemies in that harsh environment—or territorial and warlike, believing that protecting food and water sources by force is the only way to survive.

| d8 | Personality Trait |
|---|---|
| 1 | I'm much happier sleeping under the stars than in a bed in a stuffy caravanserai. |
| 2 | It's always best to help a traveler in need; one day it might be you. |
| 3 | I am slow to trust strangers, but I'm extremely loyal to my friends. |
| 4 | If there's a camel race, I'm the first to saddle up! |
| 5 | I always have a tale or poem to share at the campfire. |
| 6 | I don't like sleeping in the same place more than two nights in a row. |
| 7 | I've been troubled by strange dreams for the last month. I am determined to uncover their meaning. |
| 8 | I feel lonelier in a crowded city than I do out on the empty desert sands. |

| d6 | Ideal |
|---|---|
| 1 | Greater Good. The needs of the whole tribe outweigh those of the individuals who are part of it. (Good) |
| 2 | Nature. I must do what I can to protect the beautiful wilderness from those who would do it harm. (Neutral) |
| 3 | Tradition. I am duty-bound to follow my tribe's age-old route through the desert. (Lawful) |
| 4 | Change. Things seldom stay the same and we must always be prepared to go with the flow. (Chaotic) |
| 5 | Honor. If I behave dishonorably, my actions will bring shame upon the entire tribe. (Lawful) |
| 6 | Greed. Seize what you want if no one gives it to you freely. (Evil) |

| d6 | Bond |
|---|---|
| 1 | I am the last living member of my tribe, and I cannot let their deaths go unavenged. |
| 2 | I follow the sab siraat path of my tribe; it will bring me to the Hidden World when the time comes. |
| 3 | My best friend has been sold into slavery to the salt devils, and I need to rescue them before it is too late. |
| 4 | A nature spirit saved my life when I was dying of thirst in the desert. |
| 5 | My takoba sword is my most prized possession; for over two centuries, it's been handed down from generation to generation. |
| 6 | I have sworn revenge on the sheikh who unjustly banished me from the tribe. |

| d6 | Flaw |
|---|---|
| 1 | I enjoy the company of camels more than people. |
| 2 | I can be loud and boorish after a few wineskins. |
| 3 | If I feel insulted, I'll refuse to speak to anyone for several hours. |
| 4 | I enjoy violence and mayhem a bit too much. |
| 5 | You can't rely on me in a crisis. |
| 6 | I betrayed my brother to the followers of Boreas to save my own skin. |"""
    },
    {
        "name": "Freebooter",
        "desc": "You sailed the seas surrounding the Southlands as a freebooter, part of a pirate crew. You should come up with a name for your former ship and its captain, as well as its hunting ground and the type of ships you preyed on. Did you sail under the flag of a bloodthirsty captain, raiding coastal communities and putting everyone to the sword? Or were you part of the Istagal Raiders, the former slaves turned pirates, who battle to end the vile slave trade in the White Sea? Whatever ship you sailed on, you feel at home on board a seafaring vessel, and long periods on dry land take some getting used to.",
        "skill_proficiencies": "Athletics, Survival",
        "tool_proficiencies": "Navigator's tools, vehicles (water)",
        "languages": None,
        "equipment": "A pirate flag from your ship, several tattoos, 50 feet of rope, a set of traveler's clothes, and a belt pouch containing 10 gp",
        "feature_name": "A Friendly Face in Every Port",
        "feature_desc": "Your reputation precedes you. Whenever you visit a port city in the Southlands, you can always find someone who knows of (or has sailed on) your former ship and is familiar with its captain and crew. They are willing to provide you and your traveling companions with a roof over your head, a bed for the night, and a decent meal. If you have a reputation for cruelty and savagery, your host is probably afraid of you and will be keen for you to leave as soon as possible. Otherwise, you receive a warm welcome, and your host keeps your presence a secret if required. They may also provide you with useful information about recent goings-on in the city, including which ships have been in and out of port.",
        "suggested_characteristics": """Freebooters are a boisterous lot, but their personalities include freedom-loving mavericks and mindless thugs. Nonetheless, sailing a ship requires discipline, so freebooters tend to be reliable and aware of their role on board, even if they do their own thing once fighting breaks out. Most still yearn for the sea; some feel shame or regret for past deeds.

| d8 | Personality Trait |
|---|---|
| 1 | I'm happiest when I'm on a gentle rocking vessel, staring at the distant horizon. |
| 2 | Every time we hoisted the mainsail and raised the pirate flag, I felt butterflies in my stomach. |
| 3 | I have lovers in a dozen different ports. Most of them don't know about the others. |
| 4 | Being a pirate has taught me more swear words and bawdy jokes than I ever knew existed. I like to try them out when I meet new people. |
| 5 | One day I hope to have enough gold to fill a tub so I can bathe in it. |
| 6 | There's nothing I enjoy more than a good scrap—the bloodier, the better. |
| 7 | When a storm is blowing and the rain is lashing down on the deck, I'll be out there getting drenched. It makes me feel so alive! |
| 8 | Nothing makes me more annoyed than a badly tied knot. |

| d6 | Ideal |
|---|---|
| 1 | Freedom. No one tells me what to do or where to go. Apart from the captain. (Chaotic) |
| 2 | Greed. I'm only in it for the booty. I'll gladly stab anyone stupid enough to stand in my way. (Evil) |
| 3 | Comradery. My former shipmates are my family. I'll do anything for them. (Neutral) |
| 4 | Greater Good. No man has the right to enslave another, or to profit from slavery. (Good) |
| 5 | Code. I may be on dry land now, but I still stick to the Freebooter's Code. (Lawful) |
| 6 | Aspiration. One day I'll return to the sea as the captain of my own ship. (Any) |

| d6 | Bond |
|---|---|
| 1 | Captain Spiceblood and the Istagal Raiders rescued me from a Shibain slave ship. I owe them my life. |
| 2 | I still feel a deep attachment to my ship. Some nights I dream her figurehead is talking to me. |
| 3 | I was the ship's captain until the crew mutinied and threw me overboard to feed the sharks. I swam to a small island and survived. Vengeance will be mine! |
| 4 | 300 years ago, when the dragons attacked Roshgazi, I fled the city on a minotaur fleet bound for Capleon. I arrived back in the ruined city a few weeks ago on the same ship and can remember nothing of the voyage. |
| 5 | I fell asleep when I was supposed to be on watch, allowing our ship to be taken by surprise. I still have nightmares about my shipmates who died in the fighting. |
| 6 | One of my shipmates was captured and sold into slavery. I need to rescue them from the orchards on the Spice Coast. |

| d6 | Flaw |
|---|---|
| 1 | I'm terrified by the desert. Not enough water, far too much sand. |
| 2 | I drink too much and end up starting barroom brawls. |
| 3 | I killed one of my shipmates and took his share of the loot. |
| 4 | I take unnecessary risks and often put my friends in danger. |
| 5 | I sold captives taken at sea to jinnborn traders at Hartani Bay. |
| 6 | Most of the time, I find it impossible to tell the truth. |"""
    },
    {
        "name": "Scoundrel",
        "desc": "You were brought up in a poor neighborhood in one of the crowded towns or cities of the Southlands. You may have been lucky enough to have a leaky roof over your head, or perhaps you grew up sleeping in doorways or on the rooftops. Either way, you didn't have it easy, and you lived by your wits. While never a hardened criminal, you fell in with the wrong crowd, or you ended up in trouble for stealing food from an orange cart or clean clothes from a washing line. You're no stranger to the city watch in your hometown and have outwitted or outrun them many times.",
        "skill_proficiencies": "Athletics, Sleight of Hand",
        "tool_proficiencies": "One type of gaming set, thieves' tools",
        "languages": None,
        "equipment": "A bag of 1,000 ball bearings, a pet monkey wearing a tiny fez, a set of common clothes, and a pouch containing 10 gp",
        "feature_name": "Urban Explorer",
        "feature_desc": "You are familiar with the layout and rhythms of towns and cities. When you arrive in a new city, you can quickly locate places to stay, where to buy good quality gear, and other facilities. You can shake off pursuers when you are being chased through the streets or across the rooftops. You have a knack for leading pursuers into a crowded market filled with stalls piled high with breakable merchandise, or down a narrow alley just as a dung cart is coming in the other direction. When you make a d20 roll for a Chase Complication (see DMG), you can choose to do so with a -5 penalty, making it more likely for the participant behind you to run into a complication.",
        "suggested_characteristics": """Despite their poor upbringing, scoundrels tend to live a charmed life—never far from trouble, but usually coming out on top. Many are thrill-seekers who delight in taunting their opponents before making a flashy and daring escape. Most are generally good-hearted, but some are self-centered to the point of arrogance.

| d8 | Personality Trait |
|---|---|
| 1 | Flashing a big smile often gets me out of trouble. |
| 2 | If I can just keep them talking, it will give me time to escape. |
| 3 | I get fidgety if I have to sit still for more than ten minutes or so. |
| 4 | Whatever I do, I try to do it with style and panache. |
| 5 | I don't hold back when there's free food and drink on offer. |
| 6 | Nothing gets me more annoyed than being ignored. |
| 7 | I always sit with my back to the wall and my eyes on the exits. |
| 8 | Why walk down the street when you can run across the rooftops? |

| d6 | Ideal |
|---|---|
| 1 | Freedom. Ropes and chains are made to be broken. Locks are made to be picked. Doors are meant to be opened. (Chaotic) |
| 2 | Community. We need to look out for one another and keep everyone safe. (Lawful) |
| 3 | Charity. I share my wealth with those who need it the most. (Good) |
| 4 | Friendship. My friends matter more to me than lofty ideals. (Neutral) |
| 5 | Aspiration. One day my wondrous deeds will be known from Nuria to Sudvall. (Any) |
| 6 | Greed. I'll stop at nothing to get what I want. (Evil) |

| d6 | Bond |
|---|---|
| 1 | My elder sibling taught me how to find a safe hiding place in the city. This saved my life at least once. |
| 2 | I stole money from someone who couldn't afford to lose it and now they're destitute. One day I'll make it up to them. |
| 3 | The street kids in my hometown are my true family. |
| 4 | My mother gave me an old brass lamp. I polish it every night before going to sleep. |
| 5 | When I was young, I was too scared to leap from the tallest tower in my hometown onto the hay cart beneath. I'll try again some day. |
| 6 | A city guardsman let me go when he should have arrested me for stealing. I am forever in their debt. |

| d6 | Flaw |
|---|---|
| 1 | If there's a lever to pull, I'll pull it. |
| 2 | It's not stealing if nobody realizes it's gone. |
| 3 | If I don't like the odds, I'm out of there. |
| 4 | I often don't know when to shut up. |
| 5 | I filched a pipe from a priest of Eshu. Now I think the god has cursed me. |
| 6 | I grow angry when someone else steals the limelight. |"""
    },
    {
        "name": "Servant of the Jinn",
        "desc": "You served in the court of a powerful jinn or a genie lord. For 1,001 days you lived at court on one of the elemental planes, traveling as part of their entourage and always at their beck and call. You might be a jinnborn, in which case it was your tribe's patron jinn that called on you to serve, or you could be a Tamasheq nomad, or even a gnoll or minotaur. Whatever your heritage, you served your master as best you could and were changed forever by the otherworldly experience.",
        "skill_proficiencies": "Insight and one other skill determined by your role",
        "tool_proficiencies": "One type of tools, determined by your role",
        "languages": "Choose one from Aquan, Auran, Ignan or Terran",
        "equipment": "A set of tools or a musical instrument (one of your choice), a scroll of commendation from your former master, a set of fine clothes, a small brass lamp, and a pouch containing 10 gp",
        "feature_name": "Marked by the Jinn",
        "feature_desc": "Spending so long in the presence of the jinn or noble genies has left its mark on you. This mark isn't noticeable to most creatures, but genies and elementals sense that you have spent time at the courts of the jinn and are favorably disposed toward you when you first interact with them. Your affinity for jinn and geniekind also makes it easier for you to identify their influence on the world. You have advantage on Intelligence checks or saving throws to recognize items and magic created by genies and to see through their illusions and trickery.",
        "suggested_characteristics": """The wonders witnessed by the servants of the jinn often shape their outlook on life once they return to their homes in the Southlands. Time spent on the elemental planes can create powerful bonds or lead to unusual quirks.

| d8 | Personality Trait |
|---|---|
| 1 | I always bow deeply to show respect to those in authority. |
| 2 | I miss the hustle and bustle and splendor of the court. |
| 3 | You hear a lot of strange things when you're standing on guard outside the seraglio. |
| 4 | Cutting corners just creates more corners. Do it properly or don't do it all. |
| 5 | I worked for three days with only an hour's sleep to make sure my master's party was the most sensational ever thrown. I'd do it all over again in a heartbeat. |
| 6 | You can get away with a lot if you flash a winning smile while you do it. |
| 7 | Life was much easier when I had someone constantly telling me what to do. |
| 8 | Be careful what you wish for, particularly when an efreeti is the one granting the wish. |

| d6 | Ideal |
|---|---|
| 1 | Professionalism. I take pride in my appearance and how I conduct myself in public. (Lawful) |
| 2 | Freedom. Never again will I serve another. From now on, I answer to no one. (Chaotic) |
| 3 | Respect. All people, regardless of their station in life, deserve respect. (Good) |
| 4 | Greed. I will stop at nothing to have my own wondrous palace floating high above the clouds. (Evil) |
| 5 | Fellowship. The bonds formed between comrades when you serve together under a cruel and demanding master will never be broken. (Any) |
| 6 | Duty. It is our duty to work diligently to make something of our lives. (Neutral) |

| d6 | Bond |
|---|---|
| 1 | One day I will return to the City of Brass and bring my favorite hell hound home. |
| 2 | I will treasure the copper hookah my master gave me for my dedicated service until the day I die. |
| 3 | I yearn to look once more upon the glowing gemstones that light the tunnels through the Plane of Earth to the magnificent palace of the jinn. |
| 4 | I tasted the fruit served by Sultan Hajani the Benevolent at the Oasis of Figs once and will never forget it. |
| 5 | Although it is hard to be this far away from them, everything I do is for my family back home. |
| 6 | My true love still serves the jinn at the Court of Many-Hued Exquisite Corals. I'm determined to find a way to free them from service so we can be together. |

| d6 | Flaw |
|---|---|
| 1 | I obey those in authority without thinking. |
| 2 | 1,001 days of service has made me an expert shirker. |
| 3 | I picked up expensive tastes in food, drink, and clothes at court and am never satisfied. |
| 4 | I am incredibly indiscreet and can't be trusted with a secret. |
| 5 | Rich people don't notice if a few of their things go missing. |
| 6 | Life is very dull if you don't roll the dice. |"""
    },
    {
        "name": "Siwali Embalmer",
        "desc": "In Siwal, dealing with the dead is the livelihood of a select few families. You are a member of one of the families of Siwal's gravebinders, or you have apprenticed to one of them. You are trained in the making of shrouds, leading mourning ceremonies, and the methods one must use to consecrate both body and gravesite to prevent the dead from rising as undead. As one of the few who truly knows the streets and avenues of the Grand Necropolis, you are afforded a measure more respect than most simple gravediggers.",
        "skill_proficiencies": "Medicine, Religion",
        "tool_proficiencies": "Choose one of the following: alchemist's supplies, carpenter's tools, mason's tools, weaver's tools, or woodcarver's tools",
        "languages": None,
        "equipment": "A set of tools you are proficient with, a flask of holy water, a set of traveler's clothes, and a pouch containing 10 gp",
        "feature_name": "Secrets of the Gravekeeper",
        "feature_desc": "You spent your formative years walking the streets and alleys of graveyards and understand similar logic dictates the layout and architecture of most burial grounds. When you are in a graveyard, cemetery, or other burial site, you have advantage on Intelligence (Investigation) checks to find the location of individuals or families interred at the site. In addition, you have advantage on Intelligence (History) checks to discover information about those interred at a burial site if you have visited the site at least once. You also spent much of your life experiencing and sharing the grief of those who have lost loved ones. You are adept at bringing solace to grieving people, and when you do, you receive their gratitude in return. Whether this gratitude is given immediately or at some point in the future is at the GM's discretion. This gratitude might come as a minor gift, monetary aid, much-needed information, or other token of their appreciation.",
        "suggested_characteristics": """Siwali embalmers spent the bulk of their time ensuring the dead were respectfully prepared for eternity, which often makes them seem distant or disinterested when they must interact with the living. Dedicated to the task of properly disposing of the dead, Siwali embalmers despise the undead.

| d8 | Personality Trait |
|---|---|
| 1 | I have no reason to fear death; it is merely the next step in our journey. |
| 2 | I enjoy the quiet stillness of the dead. The living are far too busy and loud. |
| 3 | I hide my fear of death from my colleagues. |
| 4 | I cope with life's uncertainties by ensuring my life is perfectly ordered. |
| 5 | I treat the dead with respect because I hope I am shown the same kindness when my end comes. |
| 6 | Every corpse I prepare gives me reason to rejoice that I still live. |
| 7 | How I treat the tools of my trade is representative of how I treat the living. |
| 8 | Our ends could come at any time, why should I not live each day as though it was my last? |

| d6 | Ideal |
|---|---|
| 1 | Tradition. The way our society treats those who have passed to the next life is indicative of how they treat those who still live this life. (Lawful) |
| 2 | Balance. We live, then we die—it is the cycle of life. (Neutral) |
| 3 | Service. If no one steps forward to ensure the dead are interred, we will be awash in restless spirits. (Good) |
| 4 | Knowledge. The more we understand how we die, the better we can live a healthy and productive life. (Neutral) |
| 5 | Greed. Every life that ends leaves more for those who remain living. (Evil) |
| 6 | Exultation. We must beat death back and live as fully as possible before the end takes us. (Chaotic) |

| d6 | Bond |
|---|---|
| 1 | My livelihood keeps the community safe from angry spirits. |
| 2 | I am required to know the funerary traditions of all the major religions of the region to ensure every spirit passes to its proper resting place, no matter its faith. |
| 3 | When I was young, I barely survived an encounter with a zombie. |
| 4 | My family has tended to the needs of the dead for centuries. |
| 5 | I will pass my skill on to the next generation before it is time to put down my tools. |
| 6 | My deeds as a hunter and destroyer of the undead will be told and retold. |

| d6 | Flaw |
|---|---|
| 1 | After I am done with my work, I wash my hands until they are red and raw. |
| 2 | When I am questioned about my work, I get defensive and angry. |
| 3 | When I see something dying, I stare in fascination. |
| 4 | When matters of medicine or the dead are discussed, I discount anyone's contributions other than my own. |
| 5 | I dislike being in open spaces and prefer close confines. |
| 6 | When performing my work, I talk to the dead and often pause while doing so, as if giving the dead time to respond. |"""
    },
]


def convert_backgrounds() -> tuple[list, list]:
    """Convert backgrounds to Open5e format."""
    backgrounds = []
    benefits = []

    for bg_data in BACKGROUNDS:
        name = bg_data["name"]
        slug = slugify(name)
        pk = f"{DOC_KEY}_{slug}"

        # Create background entry
        background = {
            "model": "api_v2.background",
            "pk": pk,
            "fields": {
                "name": name,
                "desc": bg_data["desc"],
                "document": DOC_KEY
            }
        }
        backgrounds.append(background)

        # Create benefit entries
        # Skill proficiencies
        benefits.append({
            "model": "api_v2.backgroundbenefit",
            "pk": f"{pk}_skill-proficiencies",
            "fields": {
                "name": "Skill Proficiencies",
                "desc": bg_data["skill_proficiencies"],
                "parent": pk,
                "type": "skill_proficiency"
            }
        })

        # Tool proficiencies
        if bg_data["tool_proficiencies"]:
            benefits.append({
                "model": "api_v2.backgroundbenefit",
                "pk": f"{pk}_tool-proficiencies",
                "fields": {
                    "name": "Tool Proficiencies",
                    "desc": bg_data["tool_proficiencies"],
                    "parent": pk,
                    "type": "tool_proficiency"
                }
            })

        # Languages
        if bg_data["languages"]:
            benefits.append({
                "model": "api_v2.backgroundbenefit",
                "pk": f"{pk}_languages",
                "fields": {
                    "name": "Languages",
                    "desc": bg_data["languages"],
                    "parent": pk,
                    "type": "language"
                }
            })

        # Equipment
        benefits.append({
            "model": "api_v2.backgroundbenefit",
            "pk": f"{pk}_equipment",
            "fields": {
                "name": "Equipment",
                "desc": bg_data["equipment"],
                "parent": pk,
                "type": "equipment"
            }
        })

        # Feature
        feature_slug = slugify(bg_data["feature_name"])
        benefits.append({
            "model": "api_v2.backgroundbenefit",
            "pk": f"{pk}_{feature_slug}",
            "fields": {
                "name": bg_data["feature_name"],
                "desc": bg_data["feature_desc"],
                "parent": pk,
                "type": "feature"
            }
        })

        # Suggested characteristics
        benefits.append({
            "model": "api_v2.backgroundbenefit",
            "pk": f"{pk}_suggested-characteristics",
            "fields": {
                "name": "Suggested Characteristics",
                "desc": bg_data["suggested_characteristics"],
                "parent": pk,
                "type": "suggested_characteristics"
            }
        })

    return backgrounds, benefits


def main():
    print("=" * 60)
    print("Southlands Player's Guide Background Converter")
    print("=" * 60)

    backgrounds, benefits = convert_backgrounds()

    print(f"\nConverted {len(backgrounds)} backgrounds with {len(benefits)} benefits")

    # Save backgrounds
    bg_path = DATA_V2_DIR / "Background.json"
    with open(bg_path, "w", encoding="utf-8") as f:
        json.dump(backgrounds, f, indent=2, ensure_ascii=False)
    print(f"Saved backgrounds to {bg_path}")

    # Save benefits
    benefit_path = DATA_V2_DIR / "BackgroundBenefit.json"
    with open(benefit_path, "w", encoding="utf-8") as f:
        json.dump(benefits, f, indent=2, ensure_ascii=False)
    print(f"Saved benefits to {benefit_path}")

    print("\n" + "=" * 60)
    print("Conversion complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
