from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import generics


from django_filters import FilterSet

from api_v2 import models
from api_v2 import serializers



class SearchResultViewSet(viewsets.ModelViewSet):

    serializer_class = serializers.SearchResultSerializer

    def get_queryset(self):

        if self.request.query_params.get('query') is None:
            # Return an empty queryset
            return models.SearchResult.objects.none()
        else:
            query = self.request.query_params.get('query')

        if self.request.query_params.get("schema") is None:
            schema_version = '%'
        else:
            schema_version = self.request.query_params.get("schema")


        if self.request.query_params.get("document_pk") is None:
            document_pk= '%'
        else:
            document_pk = self.request.query_params.get("document_pk")

        if self.request.query_params.get("object_model") is None:
            object_model = '%'
        else:
            object_model = self.request.query_params.get("object_model")

        weighted_queryset = models.SearchResult.objects.raw(
            "SELECT 1 as id,rank, " +
            "snippet(search_index,5,'<span class=\"highlighted\">','</span>','...',20) as highlighted, " + 
            "* FROM search_index " + 
            "WHERE " + 
            "schema_version LIKE %s " +
            "AND document_pk LIKE %s " + 
            "AND object_model LIKE %s " + 
            "AND search_index MATCH %s" + 
            "AND rank MATCH 'bm25(1.0, 1.0, 1.0, 10.0)'"+ # This line results in a 10x weight to Name
            "ORDER BY rank",[schema_version, document_pk, object_model, query])

        return weighted_queryset
