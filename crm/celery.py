from __future__ import absolute_import, unicode_literals

import os
from django.conf import settings
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.dev_settings')
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.server_settings')

app = Celery("crm", broker=settings.CELERY_BROKER_URL)

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
