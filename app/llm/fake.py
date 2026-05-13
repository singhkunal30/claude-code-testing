"""Deterministic fake LLM client for offline development and tests."""
from __future__ import annotations

import re

from app.llm.base import DigestInput


_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "of", "in",
    "on", "at", "to", "for", "with", "by", "from", "as", "that", "this",
    "these", "those", "it", "its", "i", "you", "we", "they", "he", "she",
    "today", "learned", "learn", "learning", "about", "how", "what", "why",
    "when", "where", "if", "then", "so", "just", "can", "will", "would",
    "should", "could", "may", "might", "my", "your", "our", "their",
}


def _keywords(text: str, max_count: int = 4) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_+\-]{2,}", text.lower())
    seen: dict[str, int] = {}
    for w in words:
        if w in _STOPWORDS:
            continue
        seen[w] = seen.get(w, 0) + 1
    ranked = sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:max_count]] or ["misc"]


class FakeLLMClient:
    """Tags by extracting non-stopword keywords; digests by listing entries."""

    def tag(self, text: str) -> list[str]:
        return _keywords(text)

    def digest(self, payload: DigestInput) -> str:
        lines = [
            f"# {payload.period.capitalize()} digest "
            f"({payload.start_date} → {payload.end_date})",
            "",
            f"You logged {len(payload.entries)} entr"
            f"{'y' if len(payload.entries) == 1 else 'ies'} this {payload.period}.",
            "",
            "## Highlights",
            "",
        ]
        for e in payload.entries:
            tags = ", ".join(e.tags) if e.tags else "untagged"
            lines.append(f"- **{tags}** — {e.text}")
        return "\n".join(lines)
