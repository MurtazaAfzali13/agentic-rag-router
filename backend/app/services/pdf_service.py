"""PDF ingestion: store original bytes, locate highlights, split, upsert to Pinecone."""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.services import document_registry
from app.services.pdf_locator import (
    build_chunk_locations,
    delete_chunk_locations,
    save_chunk_locations,
)
from app.services.vectorstore import get_vectorstore

log = logging.getLogger(__name__)


class PDFProcessingError(Exception):
    pass


def _upload_path(doc_id: str) -> Path:
    return get_settings().uploads_path / f"{doc_id}.pdf"


def pdf_file_exists(doc_id: str) -> bool:
    """Return True when the original PDF bytes are on disk."""
    return _upload_path(doc_id).is_file()


def get_pdf_path(doc_id: str) -> Path | None:
    """Return the stored PDF path, or None if missing."""
    path = _upload_path(doc_id)
    return path if path.is_file() else None


def ingest_pdf(*, filename: str, content: bytes) -> dict:
    """Persist the PDF, index chunks, and write highlight sidecars."""
    s = get_settings()
    doc_id = uuid.uuid4().hex[:12]
    pdf_path = _upload_path(doc_id)

    try:
        pdf_path.write_bytes(content)

        try:
            pages = PyPDFLoader(str(pdf_path)).load()
        except Exception as exc:  # corrupted / encrypted PDFs
            raise PDFProcessingError(f"Could not read the PDF: {exc}") from exc

        pages = [p for p in pages if p.page_content.strip()]
        if not pages:
            raise PDFProcessingError(
                "No extractable text found. Scanned PDFs need OCR before they can be indexed."
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=s.chunk_size,
            chunk_overlap=s.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_documents(pages)

        locations = build_chunk_locations(pdf_path=pdf_path, chunks=chunks)
        save_chunk_locations(doc_id, locations)

        count = get_vectorstore().upsert_document(doc_id=doc_id, filename=filename, chunks=chunks)
        log.info("Indexed '%s' as %s (%d pages, %d chunks)", filename, doc_id, len(pages), count)

        record = document_registry.add_document(
            doc_id=doc_id,
            filename=filename,
            pages=len(pages),
            chunks=count,
            size_bytes=len(content),
        )
        record["has_file"] = True
        return record
    except Exception:
        # Roll back local artifacts if indexing fails mid-way.
        pdf_path.unlink(missing_ok=True)
        delete_chunk_locations(doc_id)
        raise


def delete_pdf(doc_id: str) -> bool:
    """Remove registry entry, vectors, stored PDF, and chunk sidecar."""
    if not document_registry.remove_document(doc_id):
        return False
    get_vectorstore().delete_document(doc_id)
    _upload_path(doc_id).unlink(missing_ok=True)
    delete_chunk_locations(doc_id)
    log.info("Deleted document %s (vectors, file, sidecar)", doc_id)
    return True
