"""Explicit model-router construction for offline and opt-in loopback modes."""

import os
from collections.abc import Mapping
from functools import lru_cache

import httpx2 as _httpx

from sagent_agent_core import (
    FakeModelAdapter,
    LoopbackEndpoint,
    LoopbackOpenAIChatAdapter,
    ModelAdapter,
    ModelCapability,
    ModelContractError,
    ModelRouter,
    ModelTransport,
    RemoteOpenAIChatAdapter,
    get_local_provider_profile,
)

_CLOUD_DEFAULT_URLS: dict[str, str] = {
    "openai": "https://api.openai.com",
    "anthropic": "https://api.anthropic.com",
    "deepseek": "https://api.deepseek.com",
    "groq": "https://api.groq.com",
}


def _fetch_ollama_models(base_url: str) -> list[dict]:
    """Query Ollama API for all installed models."""
    try:
        resp = _httpx.get(f"{base_url}/api/tags", timeout=5)
        if resp.status_code == 200:
            return resp.json().get("models", [])
    except Exception:
        pass
    return []


def _probe_ollama() -> list[ModelAdapter]:
    """Auto-detect Ollama at the default port and return adapters for all installed models."""
    base_url = "http://127.0.0.1:11434"
    endpoint = LoopbackEndpoint(f"{base_url}/v1", allowed_ports=frozenset({11434}))
    discovered = _fetch_ollama_models(base_url)
    adapters: list[ModelAdapter] = []
    for m in discovered:
        mname = m.get("name", "")
        if not mname:
            continue
        if mname.endswith("-embedding") or mname.endswith("-embed") or mname == "nomic-embed-text" or mname == "mxbai-embed-large" or mname == "all-minilm":
            continue
        safe_id = "ollama-" + mname.replace(":", "-").replace("/", "-").replace(".", "-")
        adapters.append(LoopbackOpenAIChatAdapter(
            endpoint, mname,
            adapter_id=safe_id,
            provider="ollama",
        ))
    return adapters


def build_model_router(environment: Mapping[str, str] | None = None) -> ModelRouter:
    """Build a router from four exact variables; no `.env` file is loaded implicitly.

    When no explicit config is given, Ollama is auto-detected on localhost:11434
    and all installed models are registered as separate adapters.
    """

    values = os.environ if environment is None else environment
    network_mode = values.get("SAGENT_NETWORK_ENABLED", "false")
    provider = values.get("SAGENT_LLM_PROVIDER", "disabled")
    base_url = values.get("SAGENT_LLM_BASE_URL", "")
    model = values.get("SAGENT_LLM_MODEL", "")
    cloud_enabled = values.get("SAGENT_CLOUD_ENABLED", "").lower() in ("true", "1", "yes")

    fake = FakeModelAdapter()
    adapters: list[ModelAdapter] = []
    allowed_transports = {ModelTransport.IN_PROCESS}
    allow_non_simulated = False
    cloud_providers_enabled = False

    # --- Cloud provider (OpenAI-compatible) ---
    if cloud_enabled:
        cloud_provider = values.get("SAGENT_CLOUD_PROVIDER", "openai")
        cloud_api_key = values.get("SAGENT_CLOUD_API_KEY", "")
        cloud_model = values.get("SAGENT_CLOUD_MODEL", "gpt-4o")
        cloud_base_url = values.get(
            "SAGENT_CLOUD_BASE_URL",
            _CLOUD_DEFAULT_URLS.get(cloud_provider, "https://api.openai.com"),
        )
        if cloud_api_key:
            safe_id = f"cloud-{cloud_provider}"
            adapters.append(RemoteOpenAIChatAdapter(
                base_url=cloud_base_url,
                model=cloud_model,
                api_key=cloud_api_key,
                adapter_id=safe_id,
                provider=cloud_provider,
            ))
            allowed_transports.add(ModelTransport.REMOTE_HTTP)
            allow_non_simulated = True
            cloud_providers_enabled = True

    # --- Local model (Ollama/LM Studio via env vars) ---
    if network_mode == "loopback":
        profile = get_local_provider_profile(provider)
        if profile is None:
            raise ModelContractError(
                "SAGENT_LLM_PROVIDER must be lm-studio or ollama in loopback mode."
            )
        if not base_url or not model:
            raise ModelContractError("Local model base URL and model identifier are required.")
        endpoint = LoopbackEndpoint(base_url, allowed_ports=frozenset({profile.port}))

        if provider == "ollama" and not model.startswith("__"):
            discovered = _fetch_ollama_models(base_url)
            if discovered:
                for m in discovered:
                    mname = m.get("name", "")
                    if not mname:
                        continue
                    safe_id = "ollama-" + mname.replace(":", "-").replace("/", "-").replace(".", "-")
                    adapters.append(LoopbackOpenAIChatAdapter(
                        endpoint, mname,
                        adapter_id=safe_id,
                        provider=profile.provider_id,
                    ))
                allowed_transports.add(ModelTransport.LOOPBACK_HTTP)
                allow_non_simulated = True
            else:
                adapters.append(LoopbackOpenAIChatAdapter(
                    endpoint, model,
                    adapter_id=profile.adapter_id,
                    provider=profile.provider_id,
                ))
                allowed_transports.add(ModelTransport.LOOPBACK_HTTP)
                allow_non_simulated = True
        else:
            adapters.append(LoopbackOpenAIChatAdapter(
                endpoint, model,
                adapter_id=profile.adapter_id,
                provider=profile.provider_id,
            ))
            allowed_transports.add(ModelTransport.LOOPBACK_HTTP)
            allow_non_simulated = True

    # --- Auto-detect Ollama (no env vars) ---
    if network_mode == "false" and provider == "disabled" and not base_url and not model and not cloud_enabled:
        ollama_adapters = _probe_ollama()
        if ollama_adapters:
            adapters.extend(ollama_adapters)
            allowed_transports.add(ModelTransport.LOOPBACK_HTTP)
            allow_non_simulated = True

    if not adapters:
        adapters.append(fake)

    default_id = next(
        (a.descriptor.adapter_id for a in adapters if a.descriptor.adapter_id != fake.descriptor.adapter_id),
        fake.descriptor.adapter_id,
    )

    return ModelRouter(
        adapters,
        {
            ModelCapability.CHAT: default_id,
            ModelCapability.CODING: default_id,
        },
        allowed_transports=frozenset(allowed_transports),
        allow_non_simulated=allow_non_simulated,
        cloud_providers_enabled=cloud_providers_enabled,
    )


@lru_cache(maxsize=1)
def get_model_router() -> ModelRouter:
    """Return a cached router whose default remains the in-process fake only."""

    return build_model_router()
