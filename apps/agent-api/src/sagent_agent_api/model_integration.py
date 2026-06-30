"""Explicit model-router construction for offline and opt-in loopback modes."""

import os
from collections.abc import Mapping
from functools import lru_cache

from sagent_agent_core import (
    FakeModelAdapter,
    LoopbackEndpoint,
    LoopbackOpenAIChatAdapter,
    ModelAdapter,
    ModelCapability,
    ModelContractError,
    ModelRouter,
    ModelTransport,
    get_local_provider_profile,
)


def build_model_router(environment: Mapping[str, str] | None = None) -> ModelRouter:
    """Build a router from four exact variables; no `.env` file is loaded implicitly."""

    values = os.environ if environment is None else environment
    network_mode = values.get("SAGENT_NETWORK_ENABLED", "false")
    provider = values.get("SAGENT_LLM_PROVIDER", "disabled")
    base_url = values.get("SAGENT_LLM_BASE_URL", "")
    model = values.get("SAGENT_LLM_MODEL", "")

    fake = FakeModelAdapter()
    adapters: list[ModelAdapter] = [fake]
    allowed_transports = {ModelTransport.IN_PROCESS}
    allow_non_simulated = False

    if network_mode == "false" and provider == "disabled" and not base_url and not model:
        pass
    else:
        if network_mode != "loopback":
            raise ModelContractError(
                "Local model configuration requires SAGENT_NETWORK_ENABLED=loopback."
            )
        profile = get_local_provider_profile(provider)
        if profile is None:
            raise ModelContractError(
                "SAGENT_LLM_PROVIDER must be lm-studio or ollama in loopback mode."
            )
        if not base_url or not model:
            raise ModelContractError("Local model base URL and model identifier are required.")
        local_adapter = LoopbackOpenAIChatAdapter(
            LoopbackEndpoint(base_url, allowed_ports=frozenset({profile.port})),
            model,
            adapter_id=profile.adapter_id,
            provider=profile.provider_id,
        )
        adapters.append(local_adapter)
        allowed_transports.add(ModelTransport.LOOPBACK_HTTP)
        allow_non_simulated = True

    return ModelRouter(
        adapters,
        {
            ModelCapability.CHAT: fake.descriptor.adapter_id,
            ModelCapability.CODING: fake.descriptor.adapter_id,
        },
        allowed_transports=frozenset(allowed_transports),
        allow_non_simulated=allow_non_simulated,
    )


@lru_cache(maxsize=1)
def get_model_router() -> ModelRouter:
    """Return a cached router whose default remains the in-process fake only."""

    return build_model_router()
