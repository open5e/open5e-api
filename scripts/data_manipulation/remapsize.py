from api_v2 import models as v2


# Run this by:
#$  python manage.py shell -c 'from scripts.data_manipulation.spell import casting_option_generate; casting_option_generate()'

def remapsize():
    print("REMAPPING SIZE FOR ITEMS")
    for item in v2.Item.objects.all():
        for size in v2.Size.objects.all():
            if item.size_integer == size.rank:
                mapped_size = size
        print("key:{} size_int:{} mapped_size:{}".format(item.key, item.size_integer, mapped_size.name))
        item.size = mapped_size
        item.save()


    print("REMAPPING SIZE FOR CREATURES")