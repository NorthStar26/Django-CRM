"""
Test script to verify email template rendering.
Run this script from the Django shell to test the email template rendering:
python manage.py shell < test_email_rendering.py
"""

import sys
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMessage
from django.conf import settings

print("Testing email template rendering...")

try:
    # Get the template
    template_name = "user_invitation_email.html"
    template = get_template(template_name)
    template_path = template.origin.name
    print(f"Template path: {template_path}")

    # Create context
    context = {
        "url": settings.DOMAIN_NAME,
        "user_email": "test@example.com",
        "complete_url": "http://localhost:8000/test-url/",
    }

    # Render template
    html_content = render_to_string(template_name, context=context)

    # Print rendered content
    print("\n\n--- RENDERED HTML CONTENT ---")
    print(html_content)
    print("--- END OF CONTENT ---\n")

    # Try sending email to console
    print("Attempting to send test email with EmailMessage...")
    email = EmailMessage(
        subject="Test Email Template",
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=["test@example.com"],
    )
    email.content_subtype = "html"  # This is required to send HTML content
    email.send()
    print("Email sent to console successfully!")

except Exception as e:
    print(f"Error testing email rendering: {e}")
    import traceback

    traceback.print_exc()

print("\nEmail test complete.")
sys.exit(0)
