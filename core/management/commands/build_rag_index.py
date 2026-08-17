"""Build (or rebuild) the RAG index from the portfolio context PDF.

Usage:
    python manage.py build_rag_index
    python manage.py build_rag_index --cv "NOCT portfolio context.pdf"
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.rag import build_index


class Command(BaseCommand):
    help = "Parse the portfolio context PDF, embed it, and write the FAISS index used by the chatbot."

    def add_arguments(self, parser):
        default_cv = settings.BASE_DIR / "NOCT portfolio context.pdf"
        parser.add_argument(
            "--cv",
            default=str(default_cv),
            help="Path to the context PDF (default: %(default)s).",
        )

    def handle(self, *args, **options):
        cv_path = Path(options["cv"])
        if not cv_path.is_absolute():
            cv_path = settings.BASE_DIR / cv_path
        if not cv_path.exists():
            raise CommandError(
                f"Context PDF not found at {cv_path}. "
                f"Place the PDF in {settings.BASE_DIR} or pass --cv <path>."
            )

        self.stdout.write(f"Parsing {cv_path} …")
        try:
            meta = build_index(cv_path, settings.RAG_INDEX_DIR)
        except Exception as exc:
            raise CommandError(f"Failed to build RAG index: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(
            f"RAG index built: chunks={meta['chunk_count']}, "
            f"dim={meta['dim']}, model={meta['model_name']}, "
            f"path={settings.RAG_INDEX_DIR}"
        ))