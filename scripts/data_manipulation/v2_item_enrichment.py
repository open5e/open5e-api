from django.template.defaultfilters import slugify

import json

from api_v2.models import Item
from api_v2.models import ItemRarity
from api_v2.models import DamageType


# Loop through all items

def main():
    for item in Item.objects.all():
        ismundane=True
        if item.rarity is not None:
            ismundane=False
        if ismundane == False:
            if item.armor is not None:
                if item.weight == 0:
                    m_item = get_mundane_version(item)
                    print("Item:{}".format(item.key))
                    print("Mundane:{}".format(m_item.key))
                    item.weight = m_item.weight
                    print("Weight:{}".format(m_item.weight))
            #new_rarity = predict_rarity(item)
            #item.rarity = new_rarity
            #print("Rarity:{}".format(new_rarity))

        item.save()

def get_mundane_version(magic_item):
    print("item:{} armor:{}".format(magic_item.key, magic_item.armor.key))
    if magic_item.armor.key == "srd_hide":
        return Item.objects.get(key='srd_hide-armor')
    if magic_item.armor.key == "srd_plate":
        return Item.objects.get(key='srd_plate-armor')
    if magic_item.armor.key == "srd_splint":
        return Item.objects.get(key='srd_splint-armor')
    if magic_item.armor.key == "srd_leather":
        return Item.objects.get(key='srd_leather-armor')
    if magic_item.armor.key == "srd_padded":
        return Item.objects.get(key='srd_padded-armor')
    if magic_item.armor.key == "srd_studded-leather":
        return Item.objects.get(key='srd_studded-leather-armor')
    mundane_item = Item.objects.get(key=str(magic_item.armor.key))

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