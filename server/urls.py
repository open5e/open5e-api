"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls import include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib import admin
from django.urls import path
from django.conf import settings

from rest_framework import routers

from api import views
from api_v2 import views as views_v2

router = routers.DefaultRouter()
#router.register(r'users', views.UserViewSet)
#router.register(r'groups', views.GroupViewSet)
router.register(r'manifest', views.ManifestViewSet)
router.register(r'spells', views.SpellViewSet)
router.register(r'spelllist',views.SpellListViewSet)
router.register(r'monsters', views.MonsterViewSet)
router.register(r'documents', views.DocumentViewSet)
router.register(r'backgrounds', views.BackgroundViewSet)
router.register(r'planes', views.PlaneViewSet)
router.register(r'sections', views.SectionViewSet)
router.register(r'feats', views.FeatViewSet)
router.register(r'conditions', views.ConditionViewSet)
router.register(r'races',views.RaceViewSet)
#router.register(r'subraces',views.SubraceViewSet)
router.register(r'classes',views.CharClassViewSet)
#router.register(r'archetypes',views.ArchetypeViewSet)
router.register(r'magicitems',views.MagicItemViewSet)
router.register(r'weapons',views.WeaponViewSet)
router.register(r'armor',views.ArmorViewSet)

#router.register('search', views.SearchView, basename="global-search")


router_v2 = routers.DefaultRouter()

router_v2.register(r'items',views_v2.ItemViewSet)
router_v2.register(r'itemsets',views_v2.ItemSetViewSet)
router_v2.register(r'itemcategories',views_v2.ItemCategoryViewSet)
router_v2.register(r'documents',views_v2.DocumentViewSet)
router_v2.register(r'licenses',views_v2.LicenseViewSet)
router_v2.register(r'publishers',views_v2.PublisherViewSet)
router_v2.register(r'weapons',views_v2.WeaponViewSet)
router_v2.register(r'armor',views_v2.ArmorViewSet)
router_v2.register(r'rulesets',views_v2.RulesetViewSet)
router_v2.register(r'backgrounds',views_v2.BackgroundViewSet)
router_v2.register(r'feats',views_v2.FeatViewSet)
router_v2.register(r'races',views_v2.RaceViewSet)
router_v2.register(r'creatures',views_v2.CreatureViewSet)
router_v2.register(r'creaturetypes',views_v2.CreatureTypeViewSet)
router_v2.register(r'creaturesets',views_v2.CreatureSetViewSet)
router_v2.register(r'damagetypes',views_v2.DamageTypeViewSet)
router_v2.register(r'languages',views_v2.LanguageViewSet)
router_v2.register(r'alignments',views_v2.AlignmentViewSet)
router_v2.register(r'conditions',views_v2.ConditionViewSet)
router_v2.register(r'spells',views_v2.SpellViewSet)
router_v2.register(r'classes',views_v2.CharacterClassViewSet)
router_v2.register(r'sizes',views_v2.SizeViewSet)
router_v2.register(r'itemrarities',views_v2.ItemRarityViewSet)
router_v2.register(r'environments',views_v2.EnvironmentViewSet)
router_v2.register(r'abilities',views_v2.AbilityViewSet)
router_v2.register(r'skills',views_v2.SkillViewSet)

router_search = routers.DefaultRouter()

router_search.register('',views_v2.SearchResultViewSet, basename='search')


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    #url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    #path('search/', include('haystack.urls')),
    path('version/', views.get_version, name="version"),
    path('v2/enums/', views_v2.get_enums, name="enums"),


    # Versioned API routes (above routes default to v1)
    path('v1/', include(router.urls)),
    #path('v1/search/', include('haystack.urls')),
    path('v2/', include(router_v2.urls)),
    path('v2/search/', include(router_search.urls))
]

if settings.DEBUG is True:
    urlpatterns.append(path('admin/', admin.site.urls))
