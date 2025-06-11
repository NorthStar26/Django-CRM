# Django CRM - Docker Development Guide

This guide helps you set up and run the Django CRM project using Docker. Choose the workflow that best fits your development style.

## Prerequisites

Before starting, make sure you have:
- **Docker Desktop** installed and running ([Download here](https://www.docker.com/products/docker-desktop))
- **Git** installed ([Download here](https://git-scm.com/downloads))
- **Python 3.9+** installed (only needed for hybrid workflow)
- A terminal/command prompt

### Quick Docker Check
Run this command to verify Docker is working:
```bash
docker --version
```
You should see something like `Docker version 20.x.x`

---

## 🚀 Option 1: Full Docker Workflow (Recommended for Beginners)

**What this does**: Runs everything (Django, database, email service, etc.) inside Docker containers. No need to install Python packages locally.

### Starting All needed contianers
```bash
# Navigate to the project folder 
#As example , basically go to your base directory 
cd c:\Users\User\Desktop\Django-CRM

# Start all services (this will download images first time - be patient!)
docker-compose -f docker/docker-compose.yml up -d
```

**What's happening**: Docker is starting 4 containers:
- 📦 Django web application (your CRM)
- 🗄️ PostgreSQL database 
- 📧 Mailhog (catches emails for testing)
- 🔄 Redis (for background tasks)

### Check if Everything Started
```bash
# See all running containers
docker-compose -f docker/docker-compose.yml ps
```

**Expected output** - all should show "Up":
```
NAME                STATUS
crm-app             Up
crm-db              Up  
crm-mailhog         Up
crm-redis           Up
```

### Access Your Application
- **Django CRM**: [http://localhost:8000](http://localhost:8000)
- **Email Testing**: [http://localhost:8025](http://localhost:8025) (see all emails sent by the app)

### View Logs (Troubleshooting)
```bash
# See what's happening in all containers
docker-compose -f docker/docker-compose.yml logs -f

# See logs for just one service
docker logs crm-app
```

### Stop Everything
```bash
# Stop all containers (keeps your data)
docker-compose -f docker/docker-compose.yml down
```

### When You Change Code
For **code changes**: Just save your files - changes appear automatically! 🎉

For **dependency changes** (if you edit `requirements.txt`):
```bash
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d
```

### Nuclear Option (Fresh Start)
If something goes wrong and you want to start completely fresh:
```bash
docker-compose -f docker/docker-compose.yml down --rmi all --volumes --remove-orphans && docker-compose -f docker/docker-compose.yml build && docker-compose -f docker/docker-compose.yml up -d
```

---

## 🛠️ Option 2: Hybrid Workflow (For Advanced Users)

**What this does**: Runs Django locally on your computer, but uses Docker for database and other services. Good for debugging and faster development.

**Prerequisites for this option**:
- Python 3.9+ installed locally
- Virtual environment set up
- Django dependencies installed locally

### Step 1: Start Supporting Services
```bash
# Navigate to project folder
cd c:\Users\User\Desktop\Django-CRM

# Start only database, Redis, and email service
docker-compose -f docker/docker-compose.yml up -d crm-db redis mailhog
```

### Step 2: Verify Services Are Running
```bash
# Check Docker services
docker-compose -f docker/docker-compose.yml ps

# Test connections (alternative methods since telnet may not be available)
# Check if ports are responding:
curl -v telnet://localhost:5432  # Database
curl -v telnet://localhost:6379  # Redis  
curl -v telnet://localhost:1025  # Email service

# Or use Docker to check service health
docker logs crm-db
docker logs crm-redis
docker logs crm-mailhog
```

### Step 3: Set Up Local Environment
Create a `.env` file in your project root with these settings:
```env
# Database settings (connects to Docker database)
DBHOST=localhost
DBPORT=5432
DBUSER=postgres
DBPASSWORD=0000

# Email settings (connects to Docker Mailhog)
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_USE_TLS=False
EMAIL_USE_SSL=False
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=crm@example.com

# Background task settings (connects to Docker Redis)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Step 4: Run Django Locally
```bash
# Apply database changes
python manage.py migrate

# (Optional) Create an admin user
python manage.py createsuperuser

# Start Django development server
python manage.py runserver
```

**Your app is now running at**: [http://localhost:8000](http://localhost:8000)

**Email testing**: [http://localhost:8025](http://localhost:8025)

### Step 5: Run Background Tasks (like email and notifications )
If your app uses background tasks, start Celery in a separate terminal:

**Windows:**
```bash
celery -A crm worker --loglevel=info --pool=solo
```

**Mac/Linux:**
```bash
celery -A crm worker --loglevel=info
```

---

---

## 🚨 Common Problems & Solutions

### "Docker containers won't start"
- **Check Docker Desktop is running** (look for Docker icon in system tray)
- **Free up disk space** (Docker needs space to download images)
- **Check ports aren't in use**:
  ```bash
  # Windows
  netstat -an | find "8000"
  netstat -an | find "5432"
  
  # Mac/Linux  
  lsof -i :8000
  lsof -i :5432
  ```

### "Can't connect to database"
- **Make sure Docker database is running**: `docker ps | grep postgres`
- **Check your .env file** has correct database settings
- **Wait a bit** - PostgreSQL takes ~10 seconds to fully start

### "Django import errors"
- **Check your Python code** for typos in import statements
- **Common fix**: Don't import `template` from `re` module - use `from django.template import Template`

### "Port already in use"
- **Something else is using the port**. Either:
  - Stop the other service
  - Or change ports in `docker-compose.yml` (e.g., change `8000:8000` to `8001:8000`)

### "Emails not working in hybrid mode"
- **Most common**: Mailhog is in Docker but Django is local
- **Solution**: Make sure `EMAIL_HOST=localhost` in your local settings
- **Test**: Visit [http://localhost:8025](http://localhost:8025) - should show Mailhog interface

### "Fresh start needed"
```bash
# Nuclear option - delete everything and start over
docker-compose -f docker/docker-compose.yml down --volumes --remove-orphans
docker system prune -f
docker-compose -f docker/docker-compose.yml up -d
```

---

## 📚 Understanding the Setup

### What Each Service Does:
- **crm-app**: Your Django web application
- **crm-db**: PostgreSQL database (stores all your data)
- **mailhog**: Email testing tool (catches emails instead of sending them)
- **redis**: Message broker (handles background tasks)
- **celery-worker**: Background task processor

### File Structure:
- `docker/docker-compose.yml`: Defines all the services
- `docker/dockerfile`: Instructions for building the Django container
- `.env`: Your local environment variables (create this yourself or in our case you can copy paste it from ENV.md  )

### Ports Used:
- **8000**: Django web application
- **5432**: PostgreSQL database
- **6379**: Redis
- **1025**: Mailhog SMTP (for sending emails)
- **8025**: Mailhog web interface (for viewing emails)

---

## 🎯 Quick Start Checklist

**For Complete Beginners (Full Docker)**:
- [ ] Install Docker Desktop
- [ ] Clone this project
- [ ] Run `docker-compose -f docker/docker-compose.yml up -d`
- [ ] Wait 2 minutes for everything to start
- [ ] Visit [http://localhost:8000](http://localhost:8000)
- [ ] Test emails at [http://localhost:8025](http://localhost:8025)

**For Developers (Hybrid)**:
- [ ] Install Docker Desktop and Python
- [ ] Clone project and set up virtual environment
- [ ] Run `docker-compose -f docker/docker-compose.yml up -d crm-db redis mailhog`
- [ ] Create `.env` file with connection settings
- [ ] Run `python manage.py migrate` and `python manage.py runserver`
- [ ] Test email functionality

**Need Help?**
- Check the logs: `docker-compose -f docker/docker-compose.yml logs -f`
- Restart services: `docker-compose -f docker/docker-compose.yml restart`
- Ask for help with specific error messages!

## 🧪 Testing Email Functionality

### Quick Email Test
1. Make sure Mailhog is running (you should see it in `docker ps`)
2. Open Django shell:
   ```bash
   # For full Docker workflow
   docker exec -it crm-app python manage.py shell
   
   # For hybrid workflow
   python manage.py shell
   ```
3. Send a test email:
   ```python
   from django.core.mail import send_mail
   
   # Send test email
   result = send_mail(
       'Test Email',
       'This is a test message!',
       'test@example.com',
       ['recipient@example.com'],
   )
   
   print("Email sent successfully!" if result else "Email failed!")
   ```
4. Check [http://localhost:8025](http://localhost:8025) - you should see your email!

### Debugging Email Issues

**If emails don't appear in Mailhog:**

1. **Check Mailhog is running**:
   ```bash
   docker ps | grep mailhog
   ```
   Should show a running container.

2. **Verify Django email settings**:
   ```bash
   # For full Docker workflow
   docker exec -it crm-app python manage.py shell
   
   # For hybrid workflow
   python manage.py shell
   ```
   ```python
   from django.conf import settings
   print("EMAIL_HOST:", settings.EMAIL_HOST)
   print("EMAIL_PORT:", settings.EMAIL_PORT)
   print("EMAIL_BACKEND:", settings.EMAIL_BACKEND)
   ```

3. **Check for error messages**: Look at your Django console output when sending emails.

4. **Test email connection**:
   ```bash
   # Check Mailhog logs
   docker logs crm-mailhog
   
   # Test web interface accessibility
   curl http://localhost:8025
   ```
