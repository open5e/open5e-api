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

from django.conf.urls import re_path, include
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

router.register('search', views.SearchView, basename="global-search")


router_v2 = routers.DefaultRouter()
if settings.V2_ENABLED:
    router_v2.register(r'items',views_v2.ItemViewSet)
    router_v2.register(r'itemsets',views_v2.ItemSetViewSet)
    router_v2.register(r'documents',views_v2.DocumentViewSet)
    router_v2.register(r'licenses',views_v2.LicenseViewSet)
    router_v2.register(r'publishers',views_v2.PublisherViewSet)
    router_v2.register(r'weapons',views_v2.WeaponViewSet)
    router_v2.register(r'armor',views_v2.ArmorViewSet)
    router_v2.register(r'rulesets',views_v2.RulesetViewSet)
    router_v2.register(r'creatures',views_v2.CreatureViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    re_path(r'^', include(router.urls)),
    #url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    re_path(r'^search/', include('haystack.urls')),
    re_path(r'^version/', views.get_version, name="version"),


    # Versioned API routes (above routes default to v1)
    re_path(r'^v1/', include(router.urls)),
    re_path(r'^v1/search/', include('haystack.urls')),
    re_path(r'^v2/', include(router_v2.urls))
]

if settings.DEBUG is True:
    urlpatterns.append(path('admin/', admin.site.urls))
