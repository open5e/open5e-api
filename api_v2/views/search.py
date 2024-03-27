from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import generics


from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers



class SearchResultViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.SearchResultSerializer
    #https://docs.djangoproject.com/en/5.0/topics/db/sql/#mapping-query-fields-to-model-fields
    
    #todo:
    # Parameterize query
    # Pull the "text" input from the querystring
    # See if 'v1' filters can be added "natively'

    def get_queryset(self):
        #query = 'cape'
        query = self.request.query_params.get('query')
        schema_version = '%'
        if self.request.query_params.get("schema") is None:
            schema_version = '%'
        else: 
            schema_version = self.request.query_params.get("schema")

        document_pk= '%'
        object_route= '%'
        queryset = models.SearchResult.objects.raw(
            "SELECT 1 as id,rank,* FROM search_index " + 
            "WHERE " + 
            "schema_version LIKE %s " +
            "AND document_pk LIKE %s " + 
            "AND object_route LIKE %s " + 
            "AND object_name MATCH %s " + 
            "ORDER BY rank",[schema_version, document_pk, object_route, query])

        return queryset
