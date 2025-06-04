@echo off
REM Script to run Celery worker with Windows-compatible settings
cd %~dp0
celery -A crm worker -l info --pool=solo
