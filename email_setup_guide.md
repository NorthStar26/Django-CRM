# Setting Up Real Email Sending in Django-CRM

This guide provides instructions for configuring Django-CRM to send real emails instead of just logging them to the console.

## Email Backend Options

Django-CRM supports the following email backends:

1. **Console Backend** (default for development)
   - Logs emails to the console instead of sending them
   - Great for development and testing

2. **SMTP Backend** (for testing real email delivery)
   - Connects to an SMTP server to send real emails
   - Good for testing and small-scale production use

3. **Amazon SES** (for production)
   - Uses Amazon's Simple Email Service
   - Excellent for high-volume email sending in production

## Configuration Steps

### Option 1: SMTP Configuration (Gmail, Office 365, etc.)

1. **Edit environment variables**

   In `docker/docker-compose.yml`, uncomment and configure the SMTP variables for both the `crm-app` and `celery` services:

   ```yaml
   - SMTP_ENABLED=true
   - EMAIL_HOST=smtp.gmail.com  # Or your SMTP server
   - EMAIL_PORT=587             # Common ports: 587 (TLS) or 465 (SSL)
   - EMAIL_USE_TLS=true         # Use false for SSL ports
   - EMAIL_HOST_USER=your-email@gmail.com
   - EMAIL_HOST_PASSWORD=your-app-password  # For Gmail, use an app password
   ```

2. **Gmail-specific setup**

   If using Gmail:
   - Enable 2FA on your Gmail account
   - Generate an "App Password" rather than using your regular password
   - Use this App Password in the `EMAIL_HOST_PASSWORD` setting

3. **Test the configuration**

   ```bash
   # SSH into the container
   docker exec -it crm-app bash
   
   # Test sending an email
   cd /app
   python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test Email', 'This is a test.', 'from@example.com', ['to@example.com'])"
   ```

### Option 2: Amazon SES (Production)

1. **Create an AWS account and set up SES**

   - Create an AWS account if you don't have one
   - Set up Amazon SES and verify your domain/email address
   - Create IAM credentials with SES permissions

2. **Configure environment variables**

   Add these to `docker/docker-compose.yml` for both `crm-app` and `celery` services:

   ```yaml
   - ENV_TYPE=prod
   - AWS_ACCESS_KEY_ID=your-aws-access-key
   - AWS_SECRET_ACCESS_KEY=your-aws-secret-key
   - AWS_BUCKET_NAME=your-bucket-name
   - AWS_SES_REGION_NAME=your-ses-region
   - AWS_SES_REGION_ENDPOINT=email.your-region.amazonaws.com
   ```

3. **Update the application settings**

   The application is already configured to use SES when `ENV_TYPE=prod`.

## Monitoring Email Delivery

1. **Check logs for email activity**

   ```bash
   docker logs crm-app
   docker logs crm-celery
   ```

2. **For Amazon SES**
   - Monitor your SES dashboard for bounces and complaints
   - Set up notifications for delivery issues

## Troubleshooting

### Common Issues:

1. **Authentication errors**
   - Check your email/password or API credentials
   - Ensure you're using app passwords for Gmail accounts with 2FA

2. **Connection errors**
   - Verify the correct port and TLS/SSL settings
   - Check if your Docker network allows outbound traffic on the required ports

3. **Rate limiting**
   - Email providers often have sending limits
   - For high-volume sending, use Amazon SES or similar services

4. **Missing emails**
   - Check spam folders
   - Verify recipient email addresses are correct

For further assistance, consult the Django email documentation: https://docs.djangoproject.com/en/stable/topics/email/
