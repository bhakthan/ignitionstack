"""LLM client wrapper — thin layer over OpenAI SDK.

Supports two backends:
  1. **Azure AI Foundry** — set ``AZURE_FOUNDRY_ENDPOINT`` and
     ``AZURE_FOUNDRY_API_KEY`` to route all calls through a Foundry
     project endpoint that exposes OpenAI-compatible models.
  2. **OpenAI direct** — the classic ``OPENAI_API_KEY`` /
     ``OPENAI_BASE_URL`` path.

When both are configured, Azure AI Foundry takes precedence.
"""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from ignition.config import IgnitionConfig


def get_client(config: IgnitionConfig) -> OpenAI:
    """Build an OpenAI-compatible client from config.

    Priority:
      1. Azure AI Foundry endpoint + API key (if both are set)
      2. Plain OpenAI (optionally with a custom base URL)
    """
    if config.has_foundry:
        return _build_foundry_client(config)
    return _build_openai_client(config)


def _build_foundry_client(config: IgnitionConfig) -> OpenAI:
    """Return an OpenAI client pointed at an Azure AI Foundry project."""
    base_url = config.azure_foundry_endpoint.rstrip("/")
    # Foundry project endpoints expose an OpenAI-compatible API under
    # /openai/deployments — the SDK handles the rest.
    if not base_url.endswith("/openai"):
        base_url = f"{base_url}/openai"
    return OpenAI(
        api_key=config.azure_foundry_api_key,
        base_url=base_url,
        default_headers={"api-key": config.azure_foundry_api_key},
    )


def _build_openai_client(config: IgnitionConfig) -> OpenAI:
    """Return a standard OpenAI client."""
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
