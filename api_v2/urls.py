from django.conf.urls import include
from django.urls import path
from rest_framework import routers

from api_v2 import views

router = routers.DefaultRouter()
router.register(r'items',views.ItemViewSet)
router.register(r'itemsets',views.ItemSetViewSet)
router.register(r'itemcategories',views.ItemCategoryViewSet)
router.register(r'documents',views.DocumentViewSet)
router.register(r'licenses',views.LicenseViewSet)
router.register(r'publishers',views.PublisherViewSet)
router.register(r'weapons',views.WeaponViewSet)
router.register(r'armor',views.ArmorViewSet)
router.register(r'gamesystems',views.GameSystemViewSet)
router.register(r'backgrounds',views.BackgroundViewSet)
router.register(r'feats',views.FeatViewSet)
router.register(r'races',views.RaceViewSet)
router.register(r'creatures',views.CreatureViewSet)
router.register(r'creaturetypes',views.CreatureTypeViewSet)
router.register(r'creaturesets',views.CreatureSetViewSet)
router.register(r'damagetypes',views.DamageTypeViewSet)
router.register(r'languages',views.LanguageViewSet)
router.register(r'alignments',views.AlignmentViewSet)
router.register(r'conditions',views.ConditionViewSet)
router.register(r'spells',views.SpellViewSet)
router.register(r'spellschools', views.SpellSchoolViewSet)
router.register(r'classes',views.CharacterClassViewSet)
router.register(r'sizes',views.SizeViewSet)
router.register(r'itemrarities',views.ItemRarityViewSet)
router.register(r'environments',views.EnvironmentViewSet)
router.register(r'abilities',views.AbilityViewSet)
router.register(r'skills',views.SkillViewSet)
router.register(r'rules', views.RuleViewSet)
router.register(r'rulesets', views.RuleSetViewSet)

search_router = routers.DefaultRouter()
search_router.register('',views.SearchResultViewSet, basename='search')

urlpatterns = [
    path('v2/', include(router.urls)),
    path('v2/search/', include(search_router.urls)),
    path('v2/enums/', views.get_enums, name="enums")
]
