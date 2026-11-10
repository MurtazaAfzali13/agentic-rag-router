"""Node 2 - Retrieval from Pinecone with enriched, numbered PDF sources."""
from __future__ import annotations

import asyncio
import logging
import re

from app.agent.state import AgentState
from app.core.config import get_settings
from app.services.pdf_locator import MATCH_QUALITY_THRESHOLD, load_chunk_locations
from app.services.vectorstore import get_vectorstore

log = logging.getLogger(__name__)

_WS_RE = re.compile(r"\s+")


def _normalize_overlap(text: str) -> set[str]:
    return set(_WS_RE.sub(" ", text.lower()).split())


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def dedupe_matches(matches: list[dict], overlap_threshold: float = 0.55) -> list[dict]:
    """Drop near-duplicate chunks (same doc + page, overlapping text); keep higher score."""
    kept: list[dict] = []
    for match in matches:
        tokens = _normalize_overlap(match.get("text", ""))
        replaced = False
        for i, existing in enumerate(kept):
            same_locus = (
                match.get("doc_id") == existing.get("doc_id")
                and match.get("page") == existing.get("page")
            )
            if not same_locus:
                continue
            if _jaccard(tokens, _normalize_overlap(existing.get("text", ""))) >= overlap_threshold:
                if float(match.get("score", 0)) > float(existing.get("score", 0)):
                    kept[i] = match
                replaced = True
                break
        if not replaced:
            kept.append(match)
    return kept


def _pdf_source(match: dict, n: int, locations: dict) -> dict:
    chunk_index = int(match.get("chunk_index", -1))
    loc = locations.get(str(chunk_index), {}) if chunk_index >= 0 else {}
    text = match.get("text", "") or ""
    match_quality = float(loc.get("match_quality", 0.0) or 0.0)
    rects = loc.get("rects") or []
    if match_quality < MATCH_QUALITY_THRESHOLD:
        rects = []

    return {
        "type": "pdf",
        "n": n,
        "doc_id": match.get("doc_id", ""),
        "chunk_index": chunk_index,
        "title": match.get("filename", "document"),
        "page": match.get("page", 0),
        "score": round(float(match.get("score", 0)), 3),
        "snippet": text,  # full passage (kept for backwards compatibility)
        "text": text,
        "rects": rects,
        "page_width": loc.get("page_width"),
        "page_height": loc.get("page_height"),
        "match_quality": match_quality,
    }


async def retriever_node(state: AgentState) -> dict:
    s = get_settings()
    query = state.get("search_query") or state["question"]

    try:
        matches = await asyncio.to_thread(get_vectorstore().query, query, s.retrieval_top_k)
    except Exception as exc:
        log.error("Pinecone retrieval failed: %s", exc)
        matches = []

    relevant = [m for m in matches if m["score"] >= s.retrieval_min_score and m["text"].strip()]
    relevant = dedupe_matches(relevant)

    # Cache sidecars per doc_id for this retrieval.
    location_cache: dict[str, dict] = {}
    sources: list[dict] = []
    enriched_docs: list[dict] = []

    for i, match in enumerate(relevant, start=1):
        doc_id = match.get("doc_id", "")
        if doc_id and doc_id not in location_cache:
            location_cache[doc_id] = await asyncio.to_thread(load_chunk_locations, doc_id)
        locations = location_cache.get(doc_id, {})
        source = _pdf_source(match, i, locations)
        sources.append(source)
        enriched_docs.append({**match, "n": i})

    return {"documents": enriched_docs, "sources": sources}
