from django.contrib import admin

from api_v2.models import *


# Register your models here.

class FromDocumentModelAdmin(admin.ModelAdmin):
    list_display = ['key', '__str__']


class ItemModelAdmin(admin.ModelAdmin):
    list_display = ['key', 'name']


class FeatBenefitInline(admin.TabularInline):
    model = FeatBenefit
    exclude = ('name',)


class FeatAdmin(admin.ModelAdmin):
    inlines = [
        FeatBenefitInline
    ]
    list_display = ['key', 'name']


class RaceTraitInline(admin.TabularInline):
    model = RaceTrait


class RaceAdmin(admin.ModelAdmin):
    inlines = [
        RaceTraitInline,
    ]


class BackgroundBenefitInline(admin.TabularInline):
    model = BackgroundBenefit


class BackgroundAdmin(admin.ModelAdmin):
    model = Background
    inlines = [
        BackgroundBenefitInline
    ]

class DamageTypeAdmin(admin.ModelAdmin):
    model = DamageType


class LanguageAdmin(admin.ModelAdmin):
    model = Language


admin.site.register(Weapon, admin_class=FromDocumentModelAdmin)
admin.site.register(Armor, admin_class=FromDocumentModelAdmin)

admin.site.register(Size)

admin.site.register(ItemCategory)
admin.site.register(ItemRarity)
admin.site.register(Item, admin_class=ItemModelAdmin)
admin.site.register(ItemSet, admin_class=FromDocumentModelAdmin)

admin.site.register(SpellSchool)
admin.site.register(Spell)

admin.site.register(Race, admin_class=RaceAdmin)

admin.site.register(Feat, admin_class=FeatAdmin)

admin.site.register(Creature)
admin.site.register(CreatureType)
admin.site.register(CreatureSet)

admin.site.register(Background, admin_class=BackgroundAdmin)

admin.site.register(Document)
admin.site.register(License)
admin.site.register(Publisher)
admin.site.register(Ruleset)

admin.site.register(DamageType)

admin.site.register(Language)

admin.site.register(Ability)
admin.site.register(Skill)

admin.site.register(Alignment)

admin.site.register(Condition)

admin.site.register(ClassFeatureItem)
admin.site.register(ClassFeature)
admin.site.register(CharacterClass)

admin.site.register(Environment)
