"""
WSGI config for server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

import newrelic.agent
newrelic_config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../newrelic.ini')
newrelic.agent.initialize(newrelic_config_file)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

application = get_wsgi_application()
