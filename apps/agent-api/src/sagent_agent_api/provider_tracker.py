"""Tracks per-provider rate limits and availability for cloud models."""

import time
from collections.abc import Generator
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class ProviderState:
    adapter_id: str
    rate_limited: bool = False
    reset_at: float = 0.0  # epoch seconds when limit resets
    consecutive_errors: int = 0
    cooldown_until: float = 0.0


class ProviderTracker:
    """Thread-safe tracker for cloud provider rate limits and availability."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._providers: dict[str, ProviderState] = {}
        # default cooldowns per error count
        self.cooldowns = [5, 15, 30, 60, 120, 300]

    def register(self, adapter_id: str) -> None:
        with self._lock:
            if adapter_id not in self._providers:
                self._providers[adapter_id] = ProviderState(adapter_id=adapter_id)

    def mark_rate_limited(self, adapter_id: str, retry_after: float = 60.0) -> None:
        with self._lock:
            state = self._providers.get(adapter_id)
            if state:
                state.rate_limited = True
                state.reset_at = time.time() + retry_after

    def mark_error(self, adapter_id: str) -> None:
        with self._lock:
            state = self._providers.get(adapter_id)
            if state:
                state.consecutive_errors += 1
                idx = min(state.consecutive_errors - 1, len(self.cooldowns) - 1)
                state.cooldown_until = time.time() + self.cooldowns[idx]

    def mark_success(self, adapter_id: str) -> None:
        with self._lock:
            state = self._providers.get(adapter_id)
            if state:
                state.consecutive_errors = 0
                state.cooldown_until = 0.0

    def is_available(self, adapter_id: str) -> bool:
        with self._lock:
            state = self._providers.get(adapter_id)
            if not state:
                return True
            if state.rate_limited and time.time() < state.reset_at:
                return False
            if state.cooldown_until > time.time():
                return False
            # Reset flags if cooldown has expired
            if state.rate_limited and time.time() >= state.reset_at:
                state.rate_limited = False
                state.reset_at = 0.0
            return True

    def get_status(self) -> dict[str, dict]:
        with self._lock:
            now = time.time()
            return {
                aid: {
                    "adapter_id": aid,
                    "available": s.rate_limited is False or now >= s.reset_at,
                    "rate_limited": s.rate_limited and now < s.reset_at,
                    "reset_in": max(0.0, s.reset_at - now) if s.rate_limited else 0.0,
                    "cooldown": max(0.0, s.cooldown_until - now),
                    "consecutive_errors": s.consecutive_errors,
                }
                for aid, s in self._providers.items()
            }

    def get_available(self, adapter_ids: list[str]) -> Generator[str, None, None]:
        """Yield adapter_ids that are currently available, in order."""
        for aid in adapter_ids:
            if self.is_available(aid):
                yield aid


# singleton
_tracker: ProviderTracker | None = None


def get_provider_tracker() -> ProviderTracker:
    global _tracker
    if _tracker is None:
        _tracker = ProviderTracker()
    return _tracker
