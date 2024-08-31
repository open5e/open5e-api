"""Search query and parameter parsing."""
from rest_framework import viewsets

from api_v2 import models
from api_v2 import serializers



class SearchResultViewSet(viewsets.ReadOnlyModelViewSet):
    """This class both define the query to get results and the structure of 
    those results for searching. Using the SearchResultSerializer for 
    structure, this makes a custom query out to a custom table built for
    full-text search."""

    serializer_class = serializers.SearchResultSerializer
    ordering_fields=[]

    def get_queryset(self):
        """Builds and runs the DB query based on querystring params"""

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

        
        columns = [
            "1 as id", # ID column is required.
            "rank",
            "snippet(search_index,4,'<span class=\"highlighted\">','</span>','...',20) as highlighted",
            "document_pk",
            "object_pk",
            "object_name",
            "object_model",
            "text",
            "schema_version"
        ]
        table_name = "search_index"
        filters = [
            "schema_version LIKE %s",
            "document_pk LIKE %s",
            "object_model LIKE %s",
            "search_index MATCH %s",
            "rank MATCH 'bm25(1.0, 1.0, 10.0)'" # This gives a 10x weight to the NAME column
        ]
        order_by = "rank"

        weighted_queryset = models.SearchResult.objects.raw(
            f"SELECT {','.join(columns)} FROM {table_name} WHERE {' AND '.join(filters)} ORDER BY {order_by}",
            [schema_version, document_pk, object_model, query])

        return weighted_queryset
