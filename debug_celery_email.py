"""
Script to debug Celery email tasks.
Run this from the terminal after starting the Docker container:
python manage.py shell < debug_celery_email.py
"""

from common.tasks import send_email_to_new_user
from common.models import Profile, User
from django.utils import timezone
import os

print("Debugging Celery email task...")

# Try to find a profile to use
profile = None

# Try to find an existing profile
try:
    profile = Profile.objects.first()
    if profile:
        print(f"Using existing profile: {profile.id} - {profile.user.email}")
    else:
        # Create a new test profile if none exists
        print("No profile found. Creating a test user and profile...")
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Create a test user
        test_user = User.objects.create(
            email="test_celery_email@example.com",
            username="test_celery_email",
            is_active=False,
        )

        # Create a test profile
        from common.models import Address, Profile

        address = Address.objects.create(
            address_line="123 Test St",
            street="Test Street",
            city="Test City",
            state="Test State",
            postcode="12345",
            country="Test Country",
        )

        profile = Profile.objects.create(
            user=test_user,
            role="ADMIN",
            address=address,
            date_of_joining=timezone.now(),
        )
        print(f"Created test profile: {profile.id} - {test_user.email}")
except Exception as e:
    print(f"Error creating test profile: {e}")
    import traceback

    traceback.print_exc()

if profile:
    # Call the task synchronously in debug mode
    print(f"\nCalling send_email_to_new_user task for profile_id: {profile.id}")
    try:
        # Force immediate task execution for debugging
        result = send_email_to_new_user(profile.id)
        print(f"Task executed synchronously. Result: {result}")
    except Exception as e:
        print(f"Error executing task: {e}")
        import traceback

        traceback.print_exc()

    # Queue the task asynchronously
    print("\nQueueing task for asynchronous execution...")
    try:
        # Queue the task for Celery
        task = send_email_to_new_user.delay(profile.id)
        print(f"Task queued with ID: {task.id}")
    except Exception as e:
        print(f"Error queueing task: {e}")
        import traceback

        traceback.print_exc()
else:
    print("No profile available for testing.")

print("\nCelery email task debug complete.")
