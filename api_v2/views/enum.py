from rest_framework.decorators import api_view
from rest_framework.response import Response

from api_v2.models import enums


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
