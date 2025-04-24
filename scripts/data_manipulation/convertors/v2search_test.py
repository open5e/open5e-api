from api_v2 import models as v2


# Run this by:
#$  python manage.py shell -c 'from scripts.data_manipulation.spell import casting_option_generate; casting_option_generate()'
def v1_search():
    query_param_text = "amulet"
    qs = v2.SearchResult.objects.extra(where={"text MATCH %s"},params={query_param_text})
    print(qs.query)
    print(qs.first().rank, qs.first().text, qs.first().route)