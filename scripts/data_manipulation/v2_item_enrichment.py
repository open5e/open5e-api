from django.template.defaultfilters import slugify

import json

from api_v2.models import Item
from api_v2.models import ItemRarity
from api_v2.models import DamageType


# Loop through all items

def main():
    for item in Item.objects.all():
        if len(item.damage_immunities.all())>0:
            item.damage_immunities.add(DamageType.objects.get(pk='poison'))
            item.damage_immunities.add(DamageType.objects.get(pk='psychic'))
        ismundane=True
        if item.rarity is None:
            if item.weapon is not None:
                if len(item.desc)>40:
                    ismundane=False
        if ismundane == False:
            #print("Key:{}".format(item.key))
            m_item = get_mundane_version(item)
            item.weight = m_item.weight
            #print("Weight:{}".format(m_item.weight))
            new_rarity = predict_rarity(item)
            item.rarity = new_rarity
            #print("Rarity:{}".format(new_rarity))

        item.save()

def get_mundane_version(magic_item):
    mundane_item = Item.objects.get(key=magic_item.weapon.key)

    return mundane_item

def predict_rarity(magic_item):
    legendary = ['vorpal','defender','luck','avenger','thunderbolts']
    very_rare = ['dancing','nine','frost','dwarven','sharpness','oathbow','speed']
    rare = ['venom','vicious','flame','dragon','giant','stealing','wounding','disruption','smiting','terror','sun']
    uncommon = ['lightning','fish']
    for word in magic_item.name.lower().split(" "):
        if word in legendary:
            return ItemRarity.objects.get(key='legendary')
        if word in very_rare:
            return ItemRarity.objects.get(key='very-rare')
        if word in rare:
            return ItemRarity.objects.get(key='rare')
        if word in uncommon:
            return ItemRarity.objects.get(key='uncommon')

    print("no rarity found for:{}".format(magic_item.key))


# For all items that are weapons, but not canonical weapons, set 
# rarity and weight.

# For all items, set damage immunities

# For all armors, confirm light/medium/heavy field


if __name__ == '__main__':
    main()