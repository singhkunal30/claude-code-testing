"""Deterministic fake LLM client for offline development and tests."""
from __future__ import annotations

import hashlib
import math
import re

from app.llm.base import DigestEntry, DigestInput


_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "of", "in",
    "on", "at", "to", "for", "with", "by", "from", "as", "that", "this",
    "these", "those", "it", "its", "i", "you", "we", "they", "he", "she",
    "today", "learned", "learn", "learning", "about", "how", "what", "why",
    "when", "where", "if", "then", "so", "just", "can", "will", "would",
    "should", "could", "may", "might", "my", "your", "our", "their",
}

EMBED_DIM = 64


def _tokens(text: str) -> list[str]:
    return [
        w
        for w in re.findall(r"[A-Za-z][A-Za-z0-9_+\-]{2,}", text.lower())
        if w not in _STOPWORDS
    ]


def _keywords(text: str, max_count: int = 4) -> list[str]:
    seen: dict[str, int] = {}
    for w in _tokens(text):
        seen[w] = seen.get(w, 0) + 1
    ranked = sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ranked[:max_count]] or ["misc"]


def _bucket(token: str) -> int:
    h = hashlib.md5(token.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % EMBED_DIM


class FakeLLMClient:
    """Tags via keywords, digests by listing entries, embeddings via hashed BOW.

    Deterministic across processes (uses MD5, not Python's PYTHONHASHSEED-
    sensitive ``hash()``). Vectors are L2-normalised so cosine similarity
    reduces to a dot product.
    """

    def tag(self, text: str) -> list[str]:
        return _keywords(text)

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * EMBED_DIM
        for tok in _tokens(text):
            vec[_bucket(tok)] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def digest(self, payload: DigestInput) -> str:
        n = len(payload.entries)
        tag_counts: dict[str, int] = {}
        for e in payload.entries:
            for t in e.tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
        recurring = [t for t, c in sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0])) if c >= 2][:5]
        themes = [t for t, _ in sorted(tag_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:3]]

        lines = [
            f"# {payload.period.capitalize()} digest "
            f"({payload.start_date} → {payload.end_date})",
            "",
            f"You logged {n} entr{'y' if n == 1 else 'ies'} this {payload.period}.",
            "",
        ]
        if themes:
            lines += ["## Themes", "", ", ".join(themes), ""]
        if recurring:
            lines += ["## Recurring tags", "", ", ".join(recurring), ""]
        lines += ["## Highlights", ""]
        for e in payload.entries:
            tags = ", ".join(e.tags) if e.tags else "untagged"
            lines.append(f"- **{tags}** — {e.text}")
        if payload.entries:
            lines += [
                "",
                "## Follow-up questions",
                "",
                f"- What surprised you most about {themes[0] if themes else 'this week'}?",
                "- Which entry would you most like to revisit next week?",
            ]
        return "\n".join(lines)

    def answer(self, question: str, entries: list[DigestEntry]) -> str:
        if not entries:
            return f"I don't have any TIL entries that touch on: {question}"
        bullets = "\n".join(f"- entry #{e.id}: {e.text}" for e in entries)
        return (
            f"Drawing from {len(entries)} of your entries about "
            f"'{question}':\n{bullets}"
        )
