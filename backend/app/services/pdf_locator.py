"""Locate chunk text on PDF pages and persist normalized highlight rectangles.

Uses pdfplumber (MIT) word boxes — never PyMuPDF (AGPL). Rectangles are stored in
sidecar JSON under data/chunks/, not in Pinecone metadata.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import pdfplumber
from rapidfuzz import fuzz

from app.core.config import get_settings

log = logging.getLogger(__name__)

MATCH_QUALITY_THRESHOLD = 0.6
_ANCHOR_TOKENS = 6
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_HYPHEN_BREAK_RE = re.compile(r"-\s*\n\s*")
_MULTI_SPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Lowercase, collapse hyphenated line breaks, strip punctuation, squash whitespace."""
    text = _HYPHEN_BREAK_RE.sub("", text)
    text = text.replace("\u00ad", "")  # soft hyphen
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    return _MULTI_SPACE_RE.sub(" ", text).strip()


def tokenize(text: str) -> list[str]:
    """Normalize then split into tokens."""
    normalized = normalize_text(text)
    return normalized.split() if normalized else []


def _sidecar_path(doc_id: str) -> Path:
    return get_settings().chunks_path / f"{doc_id}.json"


def load_chunk_locations(doc_id: str) -> dict[str, dict[str, Any]]:
    """Load the chunk-location sidecar for a document, or {} if missing."""
    path = _sidecar_path(doc_id)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Failed to read chunk sidecar for %s: %s", doc_id, exc)
        return {}


def save_chunk_locations(doc_id: str, locations: dict[str, dict[str, Any]]) -> Path:
    """Persist chunk locations to data/chunks/{doc_id}.json."""
    path = _sidecar_path(doc_id)
    path.write_text(json.dumps(locations, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def delete_chunk_locations(doc_id: str) -> None:
    """Remove the chunk sidecar if it exists."""
    path = _sidecar_path(doc_id)
    path.unlink(missing_ok=True)


def _merge_hyphenated_words(words: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    """Collapse end-of-line hyphenation into one token while keeping both boxes."""
    result: list[tuple[str, list[dict[str, Any]]]] = []
    i = 0
    while i < len(words):
        word = words[i]
        text = str(word.get("text", ""))
        if text.endswith("-") and i + 1 < len(words):
            nxt = words[i + 1]
            merged = text[:-1] + str(nxt.get("text", ""))
            tokens = tokenize(merged)
            boxes = [word, nxt]
            if tokens:
                # Hyphen joins usually produce a single token.
                result.append((tokens[0], boxes))
                for extra in tokens[1:]:
                    result.append((extra, boxes))
            i += 2
            continue
        tokens = tokenize(text)
        if tokens:
            for tok in tokens:
                result.append((tok, [word]))
        i += 1
    return result


def _find_best_window(
    page_tokens: list[str],
    chunk_tokens: list[str],
) -> tuple[int, int, float] | None:
    """Find the best contiguous window of page tokens matching the chunk sequence."""
    n = len(chunk_tokens)
    m = len(page_tokens)
    if n == 0 or m == 0:
        return None

    chunk_str = " ".join(chunk_tokens)
    anchor_n = min(_ANCHOR_TOKENS, n)
    head = " ".join(chunk_tokens[:anchor_n])
    tail = " ".join(chunk_tokens[-anchor_n:])

    best_score = 0.0
    best_span: tuple[int, int] | None = None

    min_len = max(1, n - 3)
    max_len = min(m, n + 6)

    for win_len in range(min_len, max_len + 1):
        for start in range(0, m - win_len + 1):
            window = page_tokens[start : start + win_len]
            if anchor_n >= 3:
                head_score = fuzz.ratio(head, " ".join(window[:anchor_n]))
                tail_score = fuzz.ratio(tail, " ".join(window[-anchor_n:]))
                if head_score < 65 or tail_score < 65:
                    continue
            score = fuzz.ratio(chunk_str, " ".join(window)) / 100.0
            if score > best_score:
                best_score = score
                best_span = (start, start + win_len)
            if best_score >= 0.99:
                return best_span[0], best_span[1], best_score

    if best_span is None:
        return None
    return best_span[0], best_span[1], best_score


def _boxes_to_line_rects(
    boxes: list[dict[str, Any]],
    page_width: float,
    page_height: float,
    y_tol: float = 3.0,
) -> list[dict[str, float]]:
    """Merge word boxes into per-line rectangles, normalized to 0..1 (origin top-left)."""
    if not boxes or page_width <= 0 or page_height <= 0:
        return []

    sorted_boxes = sorted(boxes, key=lambda b: (float(b["top"]), float(b["x0"])))
    lines: list[list[dict[str, Any]]] = []
    for box in sorted_boxes:
        if not lines:
            lines.append([box])
            continue
        line_top = float(lines[-1][0]["top"])
        if abs(float(box["top"]) - line_top) <= y_tol:
            lines[-1].append(box)
        else:
            lines.append([box])

    rects: list[dict[str, float]] = []
    for line in lines:
        x0 = min(float(b["x0"]) for b in line)
        x1 = max(float(b["x1"]) for b in line)
        top = min(float(b["top"]) for b in line)
        bottom = max(float(b["bottom"]) for b in line)
        rects.append(
            {
                "x": round(x0 / page_width, 6),
                "y": round(top / page_height, 6),
                "w": round((x1 - x0) / page_width, 6),
                "h": round((bottom - top) / page_height, 6),
            }
        )
    return rects


def locate_chunk_on_page(
    *,
    page: pdfplumber.page.Page,
    chunk_text: str,
    page_number: int,
) -> dict[str, Any]:
    """Align chunk text to page words and return location metadata for one chunk."""
    page_width = float(page.width)
    page_height = float(page.height)
    empty = {
        "page": page_number,
        "rects": [],
        "match_quality": 0.0,
        "page_width": page_width,
        "page_height": page_height,
    }

    chunk_tokens = tokenize(chunk_text)
    if not chunk_tokens:
        return empty

    raw_words = page.extract_words() or []
    paired = _merge_hyphenated_words(raw_words)
    if not paired:
        return empty

    page_tokens = [tok for tok, _ in paired]
    match = _find_best_window(page_tokens, chunk_tokens)
    if match is None:
        return empty

    start, end, quality = match
    if quality < MATCH_QUALITY_THRESHOLD:
        return {
            **empty,
            "match_quality": round(quality, 4),
        }

    boxes: list[dict[str, Any]] = []
    for _, word_boxes in paired[start:end]:
        boxes.extend(word_boxes)

    return {
        "page": page_number,
        "rects": _boxes_to_line_rects(boxes, page_width, page_height),
        "match_quality": round(quality, 4),
        "page_width": page_width,
        "page_height": page_height,
    }


def build_chunk_locations(*, pdf_path: Path, chunks: list[Any]) -> dict[str, dict[str, Any]]:
    """Compute highlight locations for every chunk against the stored PDF.

    Each chunk is expected to carry LangChain metadata with 0-based ``page``.
    """
    locations: dict[str, dict[str, Any]] = {}
    with pdfplumber.open(pdf_path) as pdf:
        pages = list(pdf.pages)
        for index, chunk in enumerate(chunks):
            meta = getattr(chunk, "metadata", {}) or {}
            page_idx = int(meta.get("page", 0))
            page_number = page_idx + 1
            text = getattr(chunk, "page_content", "") or ""

            if page_idx < 0 or page_idx >= len(pages):
                locations[str(index)] = {
                    "page": page_number,
                    "rects": [],
                    "match_quality": 0.0,
                    "page_width": 0.0,
                    "page_height": 0.0,
                }
                continue

            locations[str(index)] = locate_chunk_on_page(
                page=pages[page_idx],
                chunk_text=text,
                page_number=page_number,
            )

    log.info(
        "Built %d chunk locations for %s (good matches: %d)",
        len(locations),
        pdf_path.name,
        sum(1 for loc in locations.values() if loc.get("match_quality", 0) >= MATCH_QUALITY_THRESHOLD),
    )
    return locations
