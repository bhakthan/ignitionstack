"""LLM client wrapper — thin layer over OpenAI SDK."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from ignition.config import IgnitionConfig


def get_client(config: IgnitionConfig) -> OpenAI:
    """Build an OpenAI client from config."""
    kwargs: dict[str, Any] = {"api_key": config.openai_api_key}
    if config.openai_base_url:
        kwargs["base_url"] = config.openai_base_url
    return OpenAI(**kwargs)


def chat(
    client: OpenAI,
    *,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    response_format: dict[str, str] | None = None,
) -> str:
    """Send a chat completion and return the assistant message text."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def chat_json(
    client: OpenAI,
    *,
    model: str,
    system: str,
    user: str,
    temperature: float = 0.2,
    max_tokens: int = 8192,
) -> str:
    """Chat with JSON response format enforced."""
    return chat(
        client,
        model=model,
        system=system,
        user=user,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
