from __future__ import absolute_import

default_app_config = "common.apps.CommonConfig"

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from crm.celery import app as celery_app

__all__ = ("celery_app",)
