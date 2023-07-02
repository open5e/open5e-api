from django.contrib import admin

from api_v2.models import Weapon
from api_v2.models import Armor
from api_v2.models import Item, ItemSet

from api_v2.models import Document
from api_v2.models import License
from api_v2.models import Publisher
from api_v2.models import Ruleset


# Register your models here.

class FromDocumentModelAdmin(admin.ModelAdmin):
    list_display = ['key', '__str__']


admin.site.register(Weapon, admin_class=FromDocumentModelAdmin)
admin.site.register(Armor, admin_class=FromDocumentModelAdmin)

admin.site.register(Item, admin_class=FromDocumentModelAdmin)
admin.site.register(ItemSet, admin_class=FromDocumentModelAdmin)

admin.site.register(Document)
admin.site.register(License)
admin.site.register(Publisher)
admin.site.register(Ruleset)
