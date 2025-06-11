# Environment variables
SECRET_KEY="mco934$@)NHUYTC%6789"
ENV_TYPE="dev"
DOMAIN_NAME="http://localhost:8000"
FRONTEND_DOMAIN_NAME=http://localhost:3000
# AWS
AWS_BUCKET_NAME=""

AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
AWS_SES_REGION_NAME=""
AWS_SES_REGION_ENDPOINT=""


# DB
DBNAME="postgres"
DBUSER="postgres"
DBPASSWORD="0000"
DBHOST="localhost"
DBPORT="5432"

# Sentry
SENTRY_DSN=""

# Celery
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# Swagger
SWAGGER_ROOT_URL=""

#CACHES
MEMCACHELOCATION=""

# Email
EMAIL_HOST="localhost"
EMAIL_PORT="1025"
EMAIL_USE_TLS="False"
EMAIL_USE_SSL="False"
EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL="crm@example.com"
ADMIN_EMAIL="admin@example.com"