from django.contrib import admin

from api_v2.models import WeaponType
from api_v2.models import ArmorType
from api_v2.models import MagicItemType
from api_v2.models import Item

# Register your models here.

admin.site.register(WeaponType)
admin.site.register(ArmorType)
admin.site.register(MagicItemType)

admin.site.register(Item)
