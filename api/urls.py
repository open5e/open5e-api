from rest_framework import routers
from django.conf.urls import include
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api import views
from server.routers import DocumentedDefaultRouter


# DRF indexes all URLs in project when registering routes. Defining the
# `api-root` explicitly stops it getting v1 and v2 endpoints mixed up.

@api_view(['GET'])
def api_root(request, format=None):
    base = request.build_absolute_uri('/v1/')
    return Response({
        'spells': base + 'spells/',
        'spelllist': base + 'spelllist/',
        'monsters': base + 'monsters/',
        'documents': base + 'documents/',
        'backgrounds': base + 'backgrounds/',
        'planes': base + 'planes/',
        'sections': base + 'sections/',
        'feats': base + 'feats/',
        'conditions': base + 'conditions/',
        'races': base + 'races/',
        'classes': base + 'classes/',
        'magicitems': base + 'magicitems/',
        'weapons': base + 'weapons/',
        'armor': base + 'armor/',
    })


router = DocumentedDefaultRouter()
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
router.register(r'classes',views.CharClassViewSet)
router.register(r'magicitems',views.MagicItemViewSet)
router.register(r'weapons',views.WeaponViewSet)
router.register(r'armor',views.ArmorViewSet)

urlpatterns = [
    path('', api_root),
    path('v1/', api_root),              # index prevents V2 bleedthrough
    path('v1/', include(router.urls))   # actual V1 endpoints
]