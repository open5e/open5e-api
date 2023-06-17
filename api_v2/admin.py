from django.contrib import admin

from api_v2.models import WeaponType
from api_v2.models import ArmorType
from api_v2.models import MagicItemType
from api_v2.models import Item

from api_v2.models import Document
from api_v2.models import License
from api_v2.models import Publisher
from api_v2.models import Ruleset


# Register your models here.

class FromDocumentModelAdmin(admin.ModelAdmin):
    list_display = ['key','__str__']

admin.site.register(WeaponType, admin_class=FromDocumentModelAdmin)

admin.site.register(ArmorType, admin_class=FromDocumentModelAdmin)
admin.site.register(MagicItemType)

admin.site.register(Item, admin_class=FromDocumentModelAdmin)

admin.site.register(Document)
admin.site.register(License)
admin.site.register(Publisher)
admin.site.register(Ruleset)