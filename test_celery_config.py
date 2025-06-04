import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
import django
django.setup()
from django.conf import settings
print('CELERY_BROKER_URL:', settings.CELERY_BROKER_URL)
