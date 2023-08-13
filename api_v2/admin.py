from django.contrib import admin

from api_v2.models import *


# Register your models here.

class FromDocumentModelAdmin(admin.ModelAdmin):
    list_display = ['key', '__str__']


class ItemModelAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'name']

class TraitInline(admin.TabularInline):
    model = Trait

class RaceAdmin(admin.ModelAdmin):
    inlines = [
        TraitInline,
    ]

admin.site.register(Weapon, admin_class=FromDocumentModelAdmin)
admin.site.register(Armor, admin_class=FromDocumentModelAdmin)

admin.site.register(Item, admin_class=ItemModelAdmin)
admin.site.register(ItemSet, admin_class=FromDocumentModelAdmin)

admin.site.register(Race, admin_class=RaceAdmin)

#admin.site.register(Trait)
admin.site.register(Feat, admin_class=FromDocumentModelAdmin)

admin.site.register(Document)
admin.site.register(License)
admin.site.register(Publisher)
admin.site.register(Ruleset)
