#!/bin/bash

cd /app
# Run Celery with increased logging verbosity to show email content
celery -A crm worker -l debug --pool=solo
