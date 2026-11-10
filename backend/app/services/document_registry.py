"""Tiny JSON-backed registry of uploaded documents (powers the sidebar)."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings

_lock = threading.Lock()


def _file() -> Path:
    return get_settings().data_path / "documents.json"


def _read() -> list[dict]:
    path = _file()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _write(items: list[dict]) -> None:
    _file().write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")


def _has_file(doc_id: str) -> bool:
    return (get_settings().uploads_path / f"{doc_id}.pdf").is_file()


def _with_has_file(record: dict) -> dict:
    return {**record, "has_file": _has_file(record["id"])}


def list_documents() -> list[dict]:
    with _lock:
        items = sorted(_read(), key=lambda d: d["uploaded_at"], reverse=True)
    return [_with_has_file(item) for item in items]


def get_document(doc_id: str) -> dict | None:
    """Return a single registry record with ``has_file``, or None."""
    with _lock:
        for item in _read():
            if item["id"] == doc_id:
                return _with_has_file(item)
    return None


def add_document(*, doc_id: str, filename: str, pages: int, chunks: int, size_bytes: int) -> dict:
    record = {
        "id": doc_id,
        "filename": filename,
        "pages": pages,
        "chunks": chunks,
        "size_bytes": size_bytes,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    with _lock:
        items = _read()
        items.append(record)
        _write(items)
    return _with_has_file(record)


def remove_document(doc_id: str) -> bool:
    with _lock:
        items = _read()
        kept = [d for d in items if d["id"] != doc_id]
        if len(kept) == len(items):
            return False
        _write(kept)
        return True
