"""
Vercel entrypoint.

Vercel's @vercel/python build looks for either:
  - a folder named "api/" containing an "index.py" with a WSGI/ASGI app, or
  - a file pointed at by vercel.json -> builds.src

This file re-exports the Django WSGI app so Vercel can find it both ways.
"""
import os
import sys

# Add the project root to sys.path so "portfolio" and "core" resolve.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio.settings")

from portfolio.wsgi import application  # noqa: E402
