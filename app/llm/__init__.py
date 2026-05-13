"""LLM interface and default client selection.

The default client is the FakeLLMClient so the app runs without an API key.
Swap in a real client (e.g. AnthropicLLMClient) by setting it on the module.
"""
from __future__ import annotations

from app.llm.base import DigestEntry, DigestInput, LLMClient
from app.llm.fake import FakeLLMClient

_client: LLMClient = FakeLLMClient()


def set_client(client: LLMClient) -> None:
    global _client
    _client = client


def get_client() -> LLMClient:
    return _client


def auto_tag(text: str) -> list[str]:
    return get_client().tag(text)


def generate_digest(payload: DigestInput) -> str:
    return get_client().digest(payload)


def embed(text: str) -> list[float]:
    return get_client().embed(text)


def answer(question: str, entries: list[DigestEntry]) -> str:
    return get_client().answer(question, entries)


__all__ = [
    "DigestEntry",
    "DigestInput",
    "LLMClient",
    "answer",
    "auto_tag",
    "embed",
    "generate_digest",
    "get_client",
    "set_client",
]
