"""Tests for the public immutable local provider metadata contract."""

from dataclasses import FrozenInstanceError

import pytest

from sagent_agent_core import (
    LOCAL_PROVIDER_PROFILES,
    LocalProviderProfile,
    get_local_provider_profile,
)


def test_local_provider_profiles_are_exact_and_complete() -> None:
    assert tuple(
        (
            profile.provider_id,
            profile.label,
            profile.adapter_id,
            profile.host,
            profile.port,
        )
        for profile in LOCAL_PROVIDER_PROFILES
    ) == (
        ("lm-studio", "LM Studio", "local-lm-studio", "127.0.0.1", 1_234),
        ("ollama", "Ollama", "local-ollama", "127.0.0.1", 11_434),
    )


def test_local_provider_profiles_are_loopback_only() -> None:
    assert all(profile.host == "127.0.0.1" for profile in LOCAL_PROVIDER_PROFILES)
    assert all("://" not in profile.host for profile in LOCAL_PROVIDER_PROFILES)


def test_local_provider_profiles_and_collection_are_immutable() -> None:
    assert isinstance(LOCAL_PROVIDER_PROFILES, tuple)

    with pytest.raises(FrozenInstanceError):
        LOCAL_PROVIDER_PROFILES[0].port = 9999


def test_local_provider_lookup_uses_only_the_fixed_catalog() -> None:
    assert get_local_provider_profile("lm-studio") == LOCAL_PROVIDER_PROFILES[0]
    assert get_local_provider_profile("ollama") == LOCAL_PROVIDER_PROFILES[1]
    assert get_local_provider_profile("remote") is None
    assert get_local_provider_profile("") is None

    assert all(isinstance(profile, LocalProviderProfile) for profile in LOCAL_PROVIDER_PROFILES)
