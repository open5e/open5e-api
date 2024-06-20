from api_v2 import models as v2


# Run this by:
#$  python manage.py shell -c 'from scripts.data_manipulation.spell import casting_option_generate; casting_option_generate()'

def remaprarity():
    print("REMAPPING RARITY FOR ITEMS")
    for item in v2.Item.objects.all():
        if item.rarity_integer is not None:
            for rarity in v2.ItemRarity.objects.all():
                if item.rarity_integer == rarity.rank:
                    mapped_rarity = rarity
            print("key:{} size_int:{} mapped_size:{}".format(item.key, item.rarity, mapped_rarity.name))
            item.rarity = mapped_rarity
            item.save()
