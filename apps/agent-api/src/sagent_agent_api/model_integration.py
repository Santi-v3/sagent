"""Offline-only model router construction for the local Agent API."""

from functools import lru_cache

from sagent_agent_core import FakeModelAdapter, ModelCapability, ModelRouter


@lru_cache(maxsize=1)
def get_model_router() -> ModelRouter:
    """Return the in-process fake router; no network adapter is registered."""

    adapter = FakeModelAdapter()
    return ModelRouter(
        [adapter],
        {
            ModelCapability.CHAT: adapter.descriptor.adapter_id,
            ModelCapability.CODING: adapter.descriptor.adapter_id,
        },
    )
