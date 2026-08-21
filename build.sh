#!/usr/bin/env bash
# Render build script.
# Runs on every deploy: install deps, collect static, migrate,
# and seed fixtures the first time (when the DB is empty).

set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

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
