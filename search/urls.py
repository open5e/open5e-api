from django.conf.urls import include
from django.urls import path
from rest_framework import routers

from search import viewsets

search_router = routers.DefaultRouter()
search_router.register('',viewsets.SearchResultViewSet, basename='search')

urlpatterns = [
    path('v2/search/', include(search_router.urls)),
]