"""Immutable metadata for the only approved local model provider profiles."""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class LocalProviderProfile:
    """One fixed local provider identity and its loopback network boundary."""

    provider_id: str
    label: str
    adapter_id: str
    host: str
    port: int


LOCAL_PROVIDER_PROFILES: Final[tuple[LocalProviderProfile, ...]] = (
    LocalProviderProfile(
        provider_id="lm-studio",
        label="LM Studio",
        adapter_id="local-lm-studio",
        host="127.0.0.1",
        port=1_234,
    ),
    LocalProviderProfile(
        provider_id="ollama",
        label="Ollama",
        adapter_id="local-ollama",
        host="127.0.0.1",
        port=11_434,
    ),
)


def get_local_provider_profile(provider_id: str) -> LocalProviderProfile | None:
    """Return a fixed profile by ID without exposing a mutable lookup table."""

    return next(
        (
            profile
            for profile in LOCAL_PROVIDER_PROFILES
            if profile.provider_id == provider_id
        ),
        None,
    )
