# RAG Router Agent

A LangGraph agent that decides, per question, whether to answer from **your PDFs (Pinecone)**, from the **live web (Tavily)**, or directly. LLM and embeddings go through **OpenRouter**.

```
START -> analyzer --pinecone--> retriever --docs found--> generator -> END
            |                       |
            |                       +--nothing relevant--> web_search --> generator
            +--web----------------------------------------> web_search --> generator
            +--direct-------------------------------------------------> generator
```

## Structure

```
backend/app/
  agent/        state.py, graph.py, edges.py, nodes/{analyzer,retriever,web_search,generator}.py
  prompts/      router_prompt.py, generator_prompt.py   (all prompts live here)
  routes/       chat.py (SSE), documents.py, health.py
  services/     pdf_service.py, vectorstore.py (Pinecone), tavily_service.py, document_registry.py
  llm/          client.py (OpenRouter chat + embeddings)
  schemas/      request/response models
  core/         config.py, logging.py
frontend/src/
  app/          layout, page, globals.css
  components/   Sidebar, FileDropzone, DocumentList, ChatWindow, MessageBubble, RouteTrace, SourceList, ChatInput
  store/        chat-store.ts, document-store.ts (Zustand)
  lib/          api.ts (SSE streaming client), types.ts
```

## Run locally (Python 3.11+, Node 20+)

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
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

## Notes

- The Pinecone index is created automatically on first start (cosine, serverless). `EMBEDDING_DIMENSION` must match the embedding model (1536 for `openai/text-embedding-3-small`).
- Router decisions, steps and sources stream to the UI over SSE (`route`, `step`, `sources`, `token`, `done`, `error`).
- If retrieval scores fall below `RETRIEVAL_MIN_SCORE`, the agent falls back to Tavily automatically.
- Scanned PDFs have no text layer and need OCR first.
- Documents are shared in one Pinecone namespace; add per-user namespaces + auth before multi-tenant use.
