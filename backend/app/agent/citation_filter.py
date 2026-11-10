"""Strip hallucinated citation markers and filter them during SSE token streams."""
from __future__ import annotations

import re

CITATION_RE = re.compile(r"\[(\d+)\]")
_PARTIAL_CITATION_RE = re.compile(r"^\[\d*$")


def sanitize_citations(text: str, valid: set[int]) -> tuple[str, list[int]]:
    """Remove ``[n]`` markers whose n is not in ``valid``.

    Returns the cleaned text and the sorted unique list of citation numbers that remain.
    """
    used: list[int] = []

    def _replace(match: re.Match[str]) -> str:
        n = int(match.group(1))
        if n in valid:
            used.append(n)
            return match.group(0)
        return ""

    cleaned = CITATION_RE.sub(_replace, text)
    # Collapse accidental double spaces left by removals, but keep newlines intact.
    cleaned = re.sub(r"[^\S\n]{2,}", " ", cleaned)
    return cleaned, sorted(set(used))


class StreamingCitationFilter:
    """Buffer incomplete ``[n`` sequences and drop citations outside ``valid``."""

    def __init__(self, valid: set[int]) -> None:
        self.valid = valid
        self._buf = ""

    def push(self, text: str) -> str:
        """Ingest a token chunk and return text that is safe to emit."""
        if not text:
            return ""
        # When no valid citations exist, still strip any [n] the model invents.
        self._buf += text
        return self._drain(final=False)

    def flush(self) -> str:
        """Emit any remaining buffer at end of stream."""
        return self._drain(final=True)

    def _drain(self, *, final: bool) -> str:
        out: list[str] = []
        while self._buf:
            idx = self._buf.find("[")
            if idx < 0:
                out.append(self._buf)
                self._buf = ""
                break

            out.append(self._buf[:idx])
            self._buf = self._buf[idx:]

            match = CITATION_RE.match(self._buf)
            if match:
                n = int(match.group(1))
                if n in self.valid:
                    out.append(match.group(0))
                self._buf = self._buf[match.end() :]
                continue

            if _PARTIAL_CITATION_RE.match(self._buf):
                if final:
                    # Incomplete marker at EOS — emit raw text rather than inventing a chip.
                    out.append(self._buf)
                    self._buf = ""
                break

            # '[' not starting a citation — emit it and continue.
            out.append("[")
            self._buf = self._buf[1:]

        return "".join(out)
