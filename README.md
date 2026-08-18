# NOCT — Portfolio (Django)

Personal portfolio site built with Django.

## Local development

### Create the virtual environment
```bash
python -m venv .venv
```

### Activate
```powershell
.\.venv\Scripts\Activate.ps1   # PowerShell
.\.venv\Scripts\activate.bat   # cmd
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Initial setup
```bash
python manage.py loaddata fixtures.json
python manage.py makemigrations
python manage.py migrate
```

### Run the dev server
```bash
python manage.py runserver
```

Without a `DATABASE_URL` env var, the project uses a local SQLite file (`db.sqlite3`).
For production-style local dev, set `DATABASE_URL=postgres://...` and the app will
auto-switch to Postgres.

---

## Deployment to Render

This project is set up to deploy to **Render** with a managed Postgres database
and Cloudinary for media storage.

### One-time setup

1. **Create a Neon Postgres database** at <https://neon.tech>
   - Create a project, then copy the **pooled** connection string from the dashboard.
   - It looks like: `postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require`

2. **Create a Cloudinary account** at <https://cloudinary.com>
   - From the dashboard, copy `Cloud Name`, `API Key`, and `API Secret`.

3. **Generate a Django secret key**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. **Push your code to GitHub** (Render deploys from a git repo).

### Render configuration

In the Render dashboard, create a new **Web Service** pointing at your repo:

| Setting | Value |
|---|---|
| Runtime | Python |
| Build command | `./build.sh` |
| Start command | `gunicorn portfolio.wsgi:application --bind 0.0.0.0:$PORT` |
| Health check path | `/` |

### Environment variables (set in Render dashboard)

| Key | Value |
|---|---|
| `DATABASE_URL` | The Neon pooled connection string from step 1 |
| `DJANGO_SECRET_KEY` | The random secret from step 3 |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `your-app.onrender.com` (your Render URL, no protocol) |
| `CLOUDINARY_CLOUD_NAME` | from Cloudinary |
| `CLOUDINARY_API_KEY` | from Cloudinary |
| `CLOUDINARY_API_SECRET` | from Cloudinary |
| `GROQ_API` | your Groq API key (for the chat widget) |
| `GROQ_MODEL` | `groq/compound` (or your preferred model) |
| `EMAIL_HOST_USER` | SMTP user (for the contact form) |
| `EMAIL_HOST_PASSWORD` | SMTP app password |
| `ADMIN_EMAIL` | where contact-form notifications go |
| `HERO_VIDEO_URL` | optional, your hero video URL |

### First deploy

Render will run `build.sh`, which:
1. Installs requirements
2. Runs `collectstatic`
3. Runs `migrate`
4. If the DB has no projects yet, auto-loads `fixtures.json`

Subsequent deploys skip the fixture load (it's idempotent).

### Notes

- **Cold starts**: Render's free tier spins down after 15 minutes of inactivity. The
  next visitor may wait ~30 seconds for a cold start. The $7/mo plan keeps it warm.
- **Static files**: served by WhiteNoise directly from Django.
- **Media files** (uploaded thumbnails): stored on Cloudinary.
- **CSRF**: trusted origins include `https://*.onrender.com`.

---

## Project structure

```
portfolio/
├── core/                # Main Django app
├── portfolio/           # Django project (settings, urls, wsgi)
├── templates/           # Jinja-style Django templates
├── static/              # CSS / JS (collected into staticfiles/ on deploy)
├── media/               # Local media uploads (dev only — Cloudinary in prod)
├── db.sqlite3           # Local dev DB (gitignored)
├── requirements.txt
├── build.sh             # Render build script
├── Procfile             # Render start command
└── runtime.txt          # Python version pin
```
