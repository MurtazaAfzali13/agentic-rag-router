"""PDF ingestion: PyPDFLoader -> RecursiveCharacterTextSplitter -> Pinecone."""
import logging
import tempfile
import uuid
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.services import document_registry
from app.services.vectorstore import get_vectorstore

log = logging.getLogger(__name__)


class PDFProcessingError(Exception):
    pass


def ingest_pdf(*, filename: str, content: bytes) -> dict:
    s = get_settings()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        pages = PyPDFLoader(str(tmp_path)).load()
    except Exception as exc:  # corrupted / encrypted PDFs
        raise PDFProcessingError(f"Could not read the PDF: {exc}") from exc
    finally:
        tmp_path.unlink(missing_ok=True)

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

    doc_id = uuid.uuid4().hex[:12]
    count = get_vectorstore().upsert_document(doc_id=doc_id, filename=filename, chunks=chunks)
    log.info("Indexed '%s' as %s (%d pages, %d chunks)", filename, doc_id, len(pages), count)

    return document_registry.add_document(
        doc_id=doc_id,
        filename=filename,
        pages=len(pages),
        chunks=count,
        size_bytes=len(content),
    )


def delete_pdf(doc_id: str) -> bool:
    if not document_registry.remove_document(doc_id):
        return False
    get_vectorstore().delete_document(doc_id)
    return True
