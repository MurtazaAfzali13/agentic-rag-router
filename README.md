# RAG Router Agent

A LangGraph agent that decides, per question, whether to answer from **your PDFs (Pinecone)**, from the **live web (Tavily)**, or directly. LLM and embeddings go through **OpenRouter**. Answers carry inline `[n]` citations that map to exact PDF highlight rectangles or web passages.

```
START -> analyzer --pinecone--> retriever --docs found--> generator -> END
            |                       |
            |                       +--nothing relevant--> web_approval (HITL interrupt)
            +--web----------------------------------------> web_approval (HITL interrupt)
    +--direct-------------------------------------------------> generator

web_approval --YES--> web_search --> generator -> END
web_approval --NO---> fallback_not_found -> END
                 (fixed: "I could not find this information in your provided PDF documents.")
```

Human-in-the-loop: any path into live web search pauses via LangGraph `interrupt()` and an **`AsyncSqliteSaver`** checkpoint (`data/checkpoints.db`, opened in the FastAPI lifespan). Chat/resume use `astream` / `aget_state` only. The UI shows a glassmorphism confirmation modal; `POST /api/chat/resume` continues with `YES` or `NO`.

## How citations work

```
Upload PDF
  -> save bytes to data/uploads/{doc_id}.pdf
  -> PyPDFLoader (one Document per page) + RecursiveCharacterTextSplitter
  -> pdf_locator aligns each chunk to pdfplumber word boxes
  -> sidecar data/chunks/{doc_id}.json  ({chunk_index -> page, rects[], match_quality, page_w/h})
  -> embeddings upserted to Pinecone (id = {doc_id}#{chunk_index}; no rects in metadata)

Ask a question
  -> retriever / web_search emit numbered sources (n is 1-based, PDF first then web)
  -> generator must cite every grounded sentence with [n]
  -> citation_filter strips hallucinated numbers from the final answer and the SSE token stream
  -> done event includes used_citations + citations_valid
  -> frontend chips open the Source Viewer: jump to page, center the rect, pulse highlight
```

Rectangles are normalized `0..1` relative to page width/height (origin top-left): `{x, y, w, h}`. If `match_quality < 0.6`, `rects` is empty and the UI falls back to text-layer search on that page.

Documents indexed before file storage have `has_file: false` on `GET /api/documents` — the UI should prompt a re-upload for page preview.

## Structure

```
backend/app/
  agent/        state.py, graph.py, edges.py, checkpointer.py, citation_filter.py,
                nodes/{analyzer,retriever,web_approval,web_search,fallback_not_found,generator}.py
  prompts/      router_prompt.py, generator_prompt.py
  routes/       chat.py (SSE + resume), documents.py, health.py
  services/     pdf_service.py, pdf_locator.py, vectorstore.py,
                tavily_service.py, document_registry.py
  llm/          client.py (OpenRouter chat + embeddings)
  schemas/      request/response models
  core/         config.py, logging.py
frontend/src/
  app/          layout, page, globals.css
  components/   Sidebar, FileDropzone, DocumentList, ChatWindow, MessageBubble,
                RouteTrace, SourceList, ChatInput, WebSearchModal
  store/        chat-store.ts, document-store.ts (Zustand)
  lib/          api.ts (SSE streaming client), types.ts
```

## API (documents & chat)

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/api/documents` | List docs; each includes `has_file` |
| `POST` | `/api/documents/upload` | Store PDF + index + sidecar |
| `GET` | `/api/documents/{doc_id}/file` | Original PDF (`application/pdf`, inline, Range via FileResponse) |
| `DELETE` | `/api/documents/{doc_id}` | Registry + vectors + file + sidecar |
| `POST` | `/api/chat` | SSE: `route` \| `step` \| `sources` \| `token` \| `interrupt` \| `done` \| `error` |
| `POST` | `/api/chat/resume` | Body `{ thread_id, decision: "YES"\|"NO" }` — resume after HITL interrupt |

`interrupt` payload: `{ thread_id, type, message, search_query, reason, route, t }`.  
`done` payload: `{ thread_id, used_citations: number[], citations_valid: boolean, t }`.

PDF source objects include: `type, n, doc_id, chunk_index, title, page, score, snippet, text, rects, page_width, page_height, match_quality`.

## Run locally (Python 3.11+, Node 20+)

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill OPENROUTER_API_KEY, PINECONE_API_KEY, TAVILY_API_KEY
uvicorn app.main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev                 # http://localhost:3000
```

Or: `docker compose up --build` (after creating `backend/.env`).

### Tests

```bash
cd backend
pytest
```

## Notes

- The Pinecone index is created automatically on first start (cosine, serverless). `EMBEDDING_DIMENSION` must match the embedding model (1536 for `openai/text-embedding-3-small`).
- Router decisions, steps and sources stream to the UI over SSE (`route`, `step`, `sources`, `token`, `done`, `error`). Event payloads may gain fields; existing names stay stable.
- If retrieval scores fall below `RETRIEVAL_MIN_SCORE`, the agent falls back to Tavily automatically.
- Highlight geometry uses **pdfplumber** (MIT). Do not swap in PyMuPDF (AGPL) for client-shipped builds.
- Scanned PDFs have no text layer and need OCR first; alignment quality will be low and `rects` empty.
- Documents are shared in one Pinecone namespace; add per-user namespaces + auth before multi-tenant use.
