# Docker Development Workflow

## Option 1: Full Docker Workflow (everything in containers)

### Start all services (Django, Celery, DB, Redis, Mailhog, etc.)

```bash
docker-compose -f docker/docker-compose.yml up -d
```

### View logs

```bash
docker-compose -f docker/docker-compose.yml logs -f
```

### If you change dependencies (requirements.txt) or Dockerfile

```bash
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d
```

### If you want to stop and remove everything (rarely needed in dev)

```bash
docker-compose -f docker/docker-compose.yml down --rmi all --volumes --remove-orphans
```

### One-line full reset (use only if you want a clean slate)

```bash
docker-compose -f docker/docker-compose.yml down --rmi all --volumes --remove-orphans && docker-compose -f docker/docker-compose.yml build && docker-compose -f docker/docker-compose.yml up -d && docker-compose -f docker/docker-compose.yml logs -f
```

---

## Option 2: Hybrid Workflow (run Django/Celery locally, dependencies in Docker)

### Start only dependencies in Docker (DB, Redis, Mailhog)

```bash
docker-compose -f docker/docker-compose.yml up -d crm-db redis mailhog
```

### Run Django locally (in your project root)

```bash
# Apply migrations (required before first run or after model changes)
python manage.py migrate  

# (Optional) Create an admin user Django not for organization
python manage.py createsuperuser  

#Run Django locally
python manage.py runserver
```

### Run Celery locally (optional)

#### On Windows

```bash
celery -A crm worker --loglevel=info --pool=solo
```

> **Note:** The default prefork pool does not work on Windows. Use `--pool=solo` for local development.

#### On macOS/Linux

```bash
celery -A crm worker --loglevel=info
```

> **Note:** You can omit `--pool=solo` for better performance on macOS/Linux.

### Make sure your local settings point to the Docker services

- DBHOST=localhost
- DBPORT=5432
- DBUSER=postgres
- DBPASSWORD=0000
- CELERY_BROKER_URL=redis://localhost:6379/0
- CELERY_RESULT_BACKEND=redis://localhost:6379/0
- EMAIL_HOST=localhost

> These should match your .env file. If you use a .env file, you do not need to set these in your settings.py directly.

### Mailhog UI

Visit [http://localhost:8025](http://localhost:8025) in your browser.

---

**Summary:**

- For most code changes, use `up -d` and `logs -f` (full Docker) or run Django/Celery locally (hybrid).
- Only rebuild if you change dependencies or Dockerfile.
- Only use `down --rmi all --volumes --remove-orphans` for a full reset.
- Developers can choose the workflow that fits their needs.
