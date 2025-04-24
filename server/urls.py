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

from api import urls as v1_urls
from api_v2 import urls as v2_urls
from search import urls as search_urls

urlpatterns = []
urlpatterns+=v1_urls.urlpatterns
urlpatterns+=v2_urls.urlpatterns
urlpatterns+=search_urls.urlpatterns

if settings.DEBUG is True:
    urlpatterns.append(path('admin/', admin.site.urls))
