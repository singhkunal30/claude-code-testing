"""LLM interface and default client selection.

The default client is the FakeLLMClient so the app runs without an API key.
Swap in a real client (e.g. AnthropicLLMClient) by setting it on the module.
"""
from __future__ import annotations

from app.llm.base import DigestInput, LLMClient
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


__all__ = [
    "DigestInput",
    "LLMClient",
    "auto_tag",
    "generate_digest",
    "get_client",
    "set_client",
]
