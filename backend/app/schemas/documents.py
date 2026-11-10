from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: str
    filename: str
    pages: int
    chunks: int
    size_bytes: int
    uploaded_at: str
    has_file: bool = False
