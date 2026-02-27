"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls import include
from django.urls import path
from django.contrib import admin
from django.conf import settings

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from api import urls as v1_urls
from api_v2 import urls as v2_urls
from search import urls as search_urls

urlpatterns = []
urlpatterns+=v1_urls.urlpatterns
urlpatterns+=v2_urls.urlpatterns
urlpatterns+=search_urls.urlpatterns
urlpatterns+=[
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),]

if settings.DEBUG is True:
    urlpatterns.append(path('admin/', admin.site.urls))

if settings.DEBUG and not settings.TESTING:
    try:
        from debug_toolbar.toolbar import debug_toolbar_urls
        urlpatterns += debug_toolbar_urls()
    except ImportError:
        pass