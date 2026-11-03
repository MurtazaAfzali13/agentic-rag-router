import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.documents import DocumentOut
from app.services import document_registry
from app.services.pdf_service import PDFProcessingError, delete_pdf, ingest_pdf

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
async def list_documents():
    return await asyncio.to_thread(document_registry.list_documents)


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(file: UploadFile = File(...)):
    settings = get_settings()
    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF files are supported.")

    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB.")
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="The file is not a valid PDF.")

    try:
        return await asyncio.to_thread(ingest_pdf, filename=filename, content=content)
    except PDFProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: str):
    deleted = await asyncio.to_thread(delete_pdf, doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")
