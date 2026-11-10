"""Unit tests for citation sanitization and streaming filter."""
from app.agent.citation_filter import StreamingCitationFilter, sanitize_citations


def test_sanitize_keeps_valid_and_strips_invalid():
    text = "Alpha[1] beta[9] gamma[2]."
    cleaned, used = sanitize_citations(text, {1, 2})
    assert cleaned == "Alpha[1] beta gamma[2]."
    assert used == [1, 2]


def test_sanitize_empty_valid_strips_all():
    cleaned, used = sanitize_citations("Fact[1] and more[2].", set())
    assert "[1]" not in cleaned
    assert "[2]" not in cleaned
    assert used == []


def test_streaming_filter_buffers_partial_citation():
    filt = StreamingCitationFilter({1, 3})
    assert filt.push("Hello [") == "Hello "
    assert filt.push("1") == ""
    assert filt.push("] world [2] and [3].") == "[1] world  and [3]."
    assert filt.flush() == ""


def test_streaming_filter_emits_non_citation_brackets():
    filt = StreamingCitationFilter({1})
    assert filt.push("arr[i] = 1") == "arr[i] = 1"


def test_streaming_filter_flush_incomplete():
    filt = StreamingCitationFilter({1})
    assert filt.push("see [1") == "see "
    assert filt.flush() == "[1"
