#!/usr/bin/env bash
# Render build script.
# Runs on every deploy: install deps, collect static, migrate,
# and seed fixtures the first time (when the DB is empty).

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Build the RAG index from the CV PDF (chatbot knowledge base).
echo "==> Building RAG index from CV PDF..."
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')
django.setup()
from pathlib import Path
from django.conf import settings
from core.rag import build_index
pdf = Path(settings.BASE_DIR) / 'Avishek Kafle CV.pdf'
if pdf.exists():
    build_index(pdf, settings.RAG_INDEX_DIR)
    print('==> RAG index built successfully')
else:
    print('==> WARNING: CV PDF not found, chatbot will not work')
"

# Auto-seed: if there are no projects, load the bundled fixtures.
# This is idempotent — safe to run on every deploy.
PROJECT_COUNT=$(python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')
django.setup()
from core.models import VideoProject
print(VideoProject.objects.count())
" 2>/dev/null | tail -1 | tr -d '[:space:]' || echo "0")

echo "==> VideoProject count: '$PROJECT_COUNT'"

if [ "$PROJECT_COUNT" = "0" ] || [ -z "$PROJECT_COUNT" ]; then
    echo "==> Database is empty, loading fixtures.json"
    python manage.py loaddata fixtures.json
else
    echo "==> Database already has $PROJECT_COUNT projects, skipping fixture load"
fi

# Auto-create superuser if it doesn't exist yet.
python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '')
email    = os.getenv('DJANGO_SUPERUSER_EMAIL', '')
if not password:
    print('==> DJANGO_SUPERUSER_PASSWORD not set, skipping superuser creation')
elif User.objects.filter(username=username).exists():
    print(f'==> Superuser \"{username}\" already exists, skipping')
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'==> Superuser \"{username}\" created')
"
