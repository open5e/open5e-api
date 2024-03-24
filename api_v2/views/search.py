from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import generics


from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers



class SearchResultFilterSet(FilterSet):
    class Meta:
        model = models.SearchResult
        fields = {
            'schema_version': ['in', 'iexact', 'exact' ],
        }


class SearchResultViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.SearchResultSerializer
    #https://docs.djangoproject.com/en/5.0/topics/db/sql/#mapping-query-fields-to-model-fields
    def get_queryset(self):

        return models.SearchResult.objects.raw("SELECT 1 as id,rank,* FROM search_index WHERE object_name MATCH 'amulet' ORDER BY rank")

