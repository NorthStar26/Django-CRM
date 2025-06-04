"""
Utility script to test email sending in Django-CRM.

Usage:
    python manage.py shell < test_email_sending.py

This script tests the email configuration by sending a test email.
"""

import os
import sys
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

print("Email Configuration Test")
print("-----------------------")
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Test recipient - change this to your email address
recipient = os.environ.get("TEST_EMAIL_RECIPIENT") or "test@example.com"

# Test basic email sending
print(f"\nSending a plain text email to {recipient}...")
try:
    send_mail(
        "Django-CRM Test Email",
        "This is a test email from Django-CRM to verify email configuration.",
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=False,
    )
    print("Plain text email sent successfully!")
except Exception as e:
    print(f"Error sending plain text email: {e}")
    import traceback

    traceback.print_exc()

# Test HTML email sending with a template
print(f"\nSending an HTML email to {recipient}...")
try:
    # Simple context for the template
    context = {
        "user_email": recipient,
        "url": settings.DOMAIN_NAME,
        "complete_url": f"http://{settings.DOMAIN_NAME}/auth/login/",
    }

    # Try to find a template we can use
    try:
        html_content = render_to_string("user_invitation_email.html", context=context)
    except Exception as template_error:
        print(f"Could not find user_invitation_email.html template: {template_error}")
        # Use root_email_template_new.html as fallback
        try:
            html_content = render_to_string(
                "root_email_template_new.html", context=context
            )
        except Exception:
            # Last resort, create simple HTML content
            html_content = f"""
            <html>
            <body>
                <h1>Test Email</h1>
                <p>This is a test HTML email from Django-CRM to verify email configuration.</p>
                <p>Recipient: {recipient}</p>
                <p><a href="http://{settings.DOMAIN_NAME}">Visit Django-CRM</a></p>
            </body>
            </html>
            """

    msg = EmailMessage(
        "Django-CRM HTML Test Email",
        html_content,
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
    )
    msg.content_subtype = "html"
    msg.send()
    print("HTML email sent successfully!")
except Exception as e:
    print(f"Error sending HTML email: {e}")
    import traceback

    traceback.print_exc()

print(
    "\nEmail test complete. Please check the recipient inbox (or console output if using console backend)."
)
sys.exit(0)
