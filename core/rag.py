"""
RAG pipeline for the portfolio chatbot.

Knowledge source: the portfolio's context document (PDF). The pipeline is:

  1. ``parse_cv`` reads the PDF with ``pypdf``.
  2. ``chunk_text`` splits the body into ~400 char overlapping chunks.
  3. ``build_index`` embeds chunks with sentence-transformers and stores
     a FAISS index on disk under ``settings.RAG_INDEX_DIR``.
  4. ``retrieve`` embeds a query and returns the top-k chunks.
  5. ``answer`` calls Groq with the retrieved context to produce the reply.

The index is loaded lazily on first call so dev requests don't pay the
embedding-model load cost until it's actually needed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger("core.rag")

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384
CHUNK_SIZE = 400
CHUNK_OVERLAP = 60
TOP_K = 4

# Lazy singletons — populated on first access.
_embedder = None
_index_data: dict[str, Any] | None = None


# ---------- PDF parsing + chunking ----------------------------------------

def parse_cv(pdf_path: str | Path) -> str:
    """Extract plain text from every page of a PDF."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("Failed to extract a page: %s", exc)
    text = "\n\n".join(p for p in parts if p)
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks.

    Prefers paragraph boundaries (``\\n\\n``) when a paragraph fits in the
    window; otherwise splits on sentence punctuation; finally falls back
    to fixed-width sliding windows.
    """
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""

    def flush() -> None:
        nonlocal buf
        if buf:
            chunks.append(buf.strip())
        buf = ""

    for para in paragraphs:
        # If adding this paragraph keeps us under the chunk size, accumulate.
        if len(buf) + len(para) + 2 <= chunk_size:
            buf = f"{buf} {para}".strip() if buf else para
            continue

        # Otherwise flush whatever we have and start a new chunk.
        flush()
        # If a single paragraph is longer than chunk_size, split by sentence.
        if len(para) > chunk_size:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            current = ""
            for sentence in sentences:
                if len(current) + len(sentence) + 1 <= chunk_size:
                    current = f"{current} {sentence}".strip() if current else sentence
                else:
                    if current:
                        chunks.append(current.strip())
                    current = sentence
            if current:
                buf = current
        else:
            buf = para

    flush()

    # Apply overlap by re-inserting tail tokens from the previous chunk.
    if overlap > 0 and len(chunks) > 1:
        overlapped: list[str] = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped.append(chunk)
                continue
            tail = overlapped[-1][-overlap:]
            # Only glue if the resulting chunk stays under 2 * chunk_size.
            if tail and len(chunk) + len(tail) + 1 < chunk_size * 2:
                overlapped.append(f"{tail} {chunk}")
            else:
                overlapped.append(chunk)
        chunks = overlapped

    return [c for c in chunks if c]


# ---------- Index build / load --------------------------------------------

@dataclass
class _Index:
    chunks: list[str]
    meta: dict[str, Any]
    faiss: Any  # faiss.Index


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model %s …", EMBED_MODEL_NAME)
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def build_index(pdf_path: str | Path, index_dir: Path) -> dict[str, Any]:
    """Parse the CV, embed, and write the FAISS index to ``index_dir``."""
    from django.conf import settings

    index_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"CV not found at {pdf_path}")

    text = parse_cv(pdf_path)
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No extractable text found in the CV.")

    embedder = _get_embedder()
    vectors = embedder.encode(
        chunks,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype("float32")

    import faiss

    index = faiss.IndexFlatIP(EMBED_DIM)
    index.add(vectors)

    meta = {
        "model_name": EMBED_MODEL_NAME,
        "dim": EMBED_DIM,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "cv_path": str(pdf_path),
        "cv_sha256": _file_sha256(pdf_path),
        "chunk_count": len(chunks),
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }

    faiss.write_index(index, str(index_dir / "index.faiss"))
    (index_dir / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False),
        encoding="utf-8",
    )
    (index_dir / "meta.json").write_text(
        json.dumps(meta, indent=2),
        encoding="utf-8",
    )

    logger.info("RAG index built: %s chunks, dim=%s", len(chunks), EMBED_DIM)
    # Touch settings so linters don't complain — we don't actually need it.
    _ = settings.RAG_INDEX_DIR
    return meta


def load_index(index_dir: Path) -> _Index | None:
    """Load the FAISS index from disk. Returns None if files are missing."""
    global _index_data
    if _index_data is not None:
        return _index_data

    index_path = index_dir / "index.faiss"
    chunks_path = index_dir / "chunks.json"
    meta_path = index_dir / "meta.json"

    if not (index_path.exists() and chunks_path.exists() and meta_path.exists()):
        return None

    import faiss

    index = faiss.read_index(str(index_path))
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    if meta.get("model_name") != EMBED_MODEL_NAME:
        logger.error(
            "Index was built with %s but app expects %s — rebuild required.",
            meta.get("model_name"),
            EMBED_MODEL_NAME,
        )
        return None

    _index_data = {"index": index, "chunks": chunks, "meta": meta}
    return _index_data


def retrieve(query: str, top_k: int = TOP_K) -> list[dict[str, Any]]:
    """Return top-k chunks relevant to ``query``."""
    from django.conf import settings

    loaded = load_index(settings.RAG_INDEX_DIR)
    if loaded is None:
        return []

    embedder = _get_embedder()
    query_vec = embedder.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype("float32")

    scores, indices = loaded["index"].search(query_vec, top_k)
    out: list[dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk_text_value = loaded["chunks"][int(idx)]
        out.append({
            "chunk_id": int(idx),
            "snippet": chunk_text_value[:160],
            "score": float(score),
            "text": chunk_text_value,
        })
    return out


# ---------- Groq LLM ------------------------------------------------------

SYSTEM_PROMPT = (
    "You are NOCT's portfolio assistant — NOCT is a Nepal-based video editor "
    "and visual artist who works primarily in Adobe After Effects on music "
    "videos, visualizers, cinematic edits, lyric/typography visuals, atmospheric "
    "and experimental pieces, and artist promo content for musicians, rappers, "
    "singers, producers, and independent artists. "
    "Answer ONLY using the context provided below. "
    "If the answer is not in the context, say you don't know and suggest the "
    "visitor use the contact form at /contact/. "
    "Keep replies to 3 short sentences. Do not invent projects, clients, or tools."
)


def answer(question: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """Run the full RAG pipeline and return the bot reply."""
    from django.conf import settings

    started = time.perf_counter()

    chunks = retrieve(question)
    if not chunks:
        return {
            "answer": (
                "The assistant is being set up — please check back shortly. "
                "In the meantime, the contact form at /contact/ goes straight to NOCT."
            ),
            "sources": [],
            "error": "index_not_ready",
        }

    context = "\n\n---\n\n".join(c["text"] for c in chunks)

    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for turn in (history or [])[-6:]:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({
        "role": "user",
        "content": f"Question: {question}\n\nContext:\n{context}",
    })

    try:
        from groq import Groq
    except ImportError:
        logger.exception("groq SDK not installed")
        return {
            "answer": "The chat backend isn't installed correctly. Please try again later.",
            "sources": [],
            "error": "upstream_unavailable",
        }

    if not settings.GROQ_API:
        logger.error("GROQ_API is not configured")
        return {
            "answer": "The assistant isn't fully configured yet. Please use the contact form.",
            "sources": [],
            "error": "upstream_unavailable",
        }

    client = Groq(api_key=settings.GROQ_API)
    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=300,
        )
    except Exception:
        logger.exception("Groq call failed")
        return {
            "answer": "I'm having trouble reaching the assistant right now. Please try again in a moment.",
            "sources": [],
            "error": "upstream_unavailable",
        }

    answer_text = (completion.choices[0].message.content or "").strip()
    sources = [
        {"chunk_id": c["chunk_id"], "snippet": c["snippet"]}
        for c in chunks
    ]
    logger.info(
        "chat answered in %.2fs (chunks=%s, prompt=%s, answer=%s)",
        time.perf_counter() - started,
        [c["chunk_id"] for c in chunks],
        sum(len(m["content"]) for m in messages),
        len(answer_text),
    )
    return {"answer": answer_text, "sources": sources}