# Email Template Debugging Guide

This guide provides steps to debug and verify email templates in Django-CRM in both local and Docker environments.

## Approach

We've made the following changes to debug why HTML email templates aren't visible in the Docker Celery logs:

1. Enhanced the `send_email_to_new_user` task in `common/tasks.py` to:
   - Add comprehensive logging
   - Include template path information
   - Log rendered HTML content
   - Handle exceptions with proper error logging

2. Fixed the Docker Compose file to:
   - Include all necessary environment variables
   - Use the console email backend to ensure emails are logged

3. Created debugging scripts to:
   - Test email rendering directly
   - Debug Celery task execution

## Deployment & Testing Steps

### 1. Local Environment Testing

1. Run the Django server locally:
   ```
   python manage.py runserver
   ```

2. Test email template rendering:
   ```
   python manage.py shell < test_email_rendering.py
   ```

3. Test Celery task:
   ```
   celery -A crm worker --loglevel=debug
   python manage.py shell < debug_celery_email.py
   ```

### 2. Docker Environment Testing

1. Build and start the Docker containers:
   ```
   cd docker
   docker-compose up -d
   ```

2. Check Celery logs:
   ```
   docker logs crm-celery -f
   ```

3. Run the debug script in the Docker container:
   ```
   docker exec -it crm-app bash
   cd /app
   python manage.py shell < debug_celery_email.py
   ```

4. Examine the logs for:
   - Template path information
   - Rendered HTML content
   - Any errors in the template rendering process

### 3. Troubleshooting

If the HTML templates still aren't showing in the Celery logs:

1. Check Docker environment variables:
   ```
   docker exec -it crm-celery bash
   cd /app
   python -c "import os; print(os.environ.get('EMAIL_BACKEND'))"
   ```

2. Verify email backend in Django settings:
   ```
   docker exec -it crm-celery bash
   cd /app
   python -c "from django.conf import settings; print(settings.EMAIL_BACKEND)"
   ```

3. Check template accessibility:
   ```
   docker exec -it crm-celery bash
   cd /app
   python -c "from django.template.loader import get_template; print(get_template('user_invitation_email.html').origin.name)"
   ```

## Conclusion

After implementing these changes and running the tests, you should be able to:

1. See the full HTML content of emails in the Celery logs
2. Identify any issues with template loading or rendering
3. Verify that the correct email backend is being used

Once debugging is complete, you may want to reduce the logging level for production use.
