"""Unit tests for PDF chunk → highlight rectangle alignment."""
from __future__ import annotations

from pathlib import Path

import pdfplumber
import pytest
from fpdf import FPDF

from app.services.pdf_locator import (
    MATCH_QUALITY_THRESHOLD,
    build_chunk_locations,
    locate_chunk_on_page,
    normalize_text,
    tokenize,
)


PASSAGE = (
    "The quick brown fox jumps over the lazy dog near the riverbank at dawn. "
    "Researchers recorded the event carefully for the archival study."
)


def _make_pdf(path: Path, lines: list[str]) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(w=pdf.epw, h=8, text=line)
        pdf.ln(4)
    pdf.output(str(path))


def test_normalize_and_tokenize_collapse_hyphen_breaks():
    assert normalize_text("Hello,\nWorld!") == "hello world"
    assert tokenize("State-of-the-art methods") == ["state", "of", "the", "art", "methods"]
    assert tokenize("exam-\nple text") == ["example", "text"]


def test_locate_chunk_finds_rects(tmp_path: Path):
    pdf_path = tmp_path / "sample.pdf"
    _make_pdf(pdf_path, [PASSAGE, "Unrelated footer material appears here."])

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        result = locate_chunk_on_page(page=page, chunk_text=PASSAGE, page_number=1)

    assert result["page"] == 1
    assert result["page_width"] > 0
    assert result["page_height"] > 0
    assert result["match_quality"] >= MATCH_QUALITY_THRESHOLD
    assert len(result["rects"]) >= 1
    for rect in result["rects"]:
        assert 0 <= rect["x"] <= 1
        assert 0 <= rect["y"] <= 1
        assert 0 < rect["w"] <= 1
        assert 0 < rect["h"] <= 1


def test_locate_chunk_low_quality_when_missing(tmp_path: Path):
    pdf_path = tmp_path / "sample.pdf"
    _make_pdf(pdf_path, ["Completely different content on this page."])

    with pdfplumber.open(pdf_path) as pdf:
        result = locate_chunk_on_page(
            page=pdf.pages[0],
            chunk_text="This passage does not exist anywhere in the document at all.",
            page_number=1,
        )

    assert result["rects"] == []
    assert result["match_quality"] < MATCH_QUALITY_THRESHOLD


def test_build_chunk_locations_sidecar_shape(tmp_path: Path):
    pdf_path = tmp_path / "multi.pdf"
    _make_pdf(pdf_path, [PASSAGE])

    class FakeChunk:
        def __init__(self, text: str, page: int) -> None:
            self.page_content = text
            self.metadata = {"page": page}

    chunks = [FakeChunk(PASSAGE, 0)]
    locations = build_chunk_locations(pdf_path=pdf_path, chunks=chunks)
    assert "0" in locations
    assert locations["0"]["page"] == 1
    assert "rects" in locations["0"]
    assert "match_quality" in locations["0"]
