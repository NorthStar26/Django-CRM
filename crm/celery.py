from __future__ import absolute_import, unicode_literals

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")

app = Celery("crm")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Enable task result tracing and logging
app.conf.task_store_errors_even_if_ignored = True
app.conf.worker_log_color = True
app.conf.task_track_started = True
app.conf.worker_send_task_events = True
