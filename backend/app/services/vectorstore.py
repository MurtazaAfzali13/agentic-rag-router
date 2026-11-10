"""Pinecone wrapper: index bootstrap, upsert, similarity query, delete."""
import logging
import time
from functools import lru_cache

from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec

from app.core.config import get_settings
from app.llm.client import get_embeddings

log = logging.getLogger(__name__)
_BATCH = 100


class VectorStore:
    def __init__(self) -> None:
        s = get_settings()
        self._s = s
        self._pc = Pinecone(api_key=s.pinecone_api_key)
        self._index = self._ensure_index()

    def _ensure_index(self):
        s = self._s
        if not self._pc.has_index(s.pinecone_index_name):
            log.info("Creating Pinecone index '%s' (dim=%s)", s.pinecone_index_name, s.embedding_dimension)
            self._pc.create_index(
                name=s.pinecone_index_name,
                dimension=s.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=s.pinecone_cloud, region=s.pinecone_region),
            )
            while not self._pc.describe_index(s.pinecone_index_name).status["ready"]:
                time.sleep(1)
        return self._pc.Index(s.pinecone_index_name)

    def upsert_document(self, *, doc_id: str, filename: str, chunks: list[Document]) -> int:
        texts = [c.page_content for c in chunks]
        vectors = get_embeddings().embed_documents(texts)
        records = []
        for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
            records.append(
                {
                    "id": f"{doc_id}#{i}",
                    "values": vec,
                    "metadata": {
                        "text": chunk.page_content,
                        "doc_id": doc_id,
                        "filename": filename,
                        "page": int(chunk.metadata.get("page", 0)) + 1,
                        "chunk_index": i,
                    },
                }
            )
        for start in range(0, len(records), _BATCH):
            self._index.upsert(vectors=records[start : start + _BATCH], namespace=self._s.pinecone_namespace)
        return len(records)

    def query(self, text: str, top_k: int) -> list[dict]:
        vector = get_embeddings().embed_query(text)
        res = self._index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            namespace=self._s.pinecone_namespace,
        )
        matches = []
        for m in res.matches:
            md = m.metadata or {}
            # Prefer metadata chunk_index; fall back to parsing the vector id `{doc_id}#{i}`.
            chunk_index = md.get("chunk_index")
            if chunk_index is None:
                vid = getattr(m, "id", "") or ""
                try:
                    chunk_index = int(str(vid).rsplit("#", 1)[-1])
                except ValueError:
                    chunk_index = -1
            matches.append(
                {
                    "text": md.get("text", ""),
                    "filename": md.get("filename", "document"),
                    "doc_id": md.get("doc_id", ""),
                    "page": int(md.get("page", 0)),
                    "chunk_index": int(chunk_index),
                    "score": float(m.score),
                }
            )
        return matches

    def delete_document(self, doc_id: str) -> None:
        ns = self._s.pinecone_namespace
        for id_batch in self._index.list(prefix=f"{doc_id}#", namespace=ns):
            if id_batch:
                self._index.delete(ids=list(id_batch), namespace=ns)


@lru_cache
def get_vectorstore() -> VectorStore:
    return VectorStore()
