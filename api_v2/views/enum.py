from rest_framework.decorators import api_view
from rest_framework.response import Response

from api_v2.models import enums

from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, extend_schema_view, extend_schema, inline_serializer

@extend_schema(
    description="API endpoint for enums.",
    responses={
        200: serializers.ListSerializer(
            child=serializers.DictField(
                child=serializers.CharField()
            )
        )
    }
)
@api_view()
def get_enums(_):
    """
    API endpoint for enums.
    """
    e = []
    for key,value in enums.__dict__.items():
        if not key.startswith("__"):
            e.append({key:value})

    return Response(e)
