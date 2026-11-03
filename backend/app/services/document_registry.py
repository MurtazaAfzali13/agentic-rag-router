"""Tiny JSON-backed registry of uploaded documents (powers the sidebar)."""
import json
import threading
from datetime import datetime, timezone

from app.core.config import get_settings

_lock = threading.Lock()


def _file():
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


def list_documents() -> list[dict]:
    with _lock:
        return sorted(_read(), key=lambda d: d["uploaded_at"], reverse=True)


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
    return record


def remove_document(doc_id: str) -> bool:
    with _lock:
        items = _read()
        kept = [d for d in items if d["id"] != doc_id]
        if len(kept) == len(items):
            return False
        _write(kept)
        return True
