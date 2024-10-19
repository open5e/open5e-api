from rest_framework import routers

from api import views

router = routers.DefaultRouter()
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
router.register(r'classes',views.CharClassViewSet)
router.register(r'magicitems',views.MagicItemViewSet)
router.register(r'weapons',views.WeaponViewSet)
router.register(r'armor',views.ArmorViewSet)
