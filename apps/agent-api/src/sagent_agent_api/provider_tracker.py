"""Tracks per-provider rate limits, availability, and usage history with cost estimation."""

import time
import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class UsageEntry:
    id: str
    timestamp: float
    adapter_id: str
    model: str
    provider: str
    transport: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    success: bool
    error: str = ""


# Known model pricing per 1M tokens in USD
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4": (30.00, 60.00),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "o1": (15.00, 60.00),
    "o1-mini": (3.00, 12.00),
    "o3-mini": (1.10, 4.40),
    # Anthropic
    "claude-3-opus": (15.00, 75.00),
    "claude-3.5-sonnet": (3.00, 15.00),
    "claude-3.5-haiku": (0.80, 4.00),
    "claude-4": (15.00, 75.00),
    # Google
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.0-pro": (2.00, 8.00),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemma-4": (0.00, 0.00),  # local
    # Meta
    "llama-4": (0.00, 0.00),
    "llama-3.3": (0.00, 0.00),
    "qwen": (0.00, 0.00),
    "deepseek": (0.00, 0.00),
    "mistral": (0.00, 0.00),
    "phi-4": (0.00, 0.00),
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD using known pricing per 1M tokens."""
    for key, (in_price, out_price) in MODEL_PRICING.items():
        if key in model.lower():
            return (input_tokens / 1_000_000 * in_price) + (output_tokens / 1_000_000 * out_price)
    return 0.0


@dataclass
class ProviderState:
    adapter_id: str
    rate_limited: bool = False
    reset_at: float = 0.0
    consecutive_errors: int = 0
    cooldown_until: float = 0.0


class ProviderTracker:
    """Thread-safe tracker for cloud provider rate limits and usage history."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._providers: dict[str, ProviderState] = {}
        self._history: list[UsageEntry] = []
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

    def log_usage(
        self,
        adapter_id: str,
        model: str,
        provider: str,
        transport: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ms: int = 0,
        success: bool = True,
        error: str = "",
    ) -> None:
        """Record a model usage event."""
        entry = UsageEntry(
            id=uuid.uuid4().hex[:12],
            timestamp=time.time(),
            adapter_id=adapter_id,
            model=model,
            provider=provider,
            transport=transport,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            success=success,
            error=error,
        )
        with self._lock:
            self._history.append(entry)
            # Keep last 5000 entries to avoid unbounded memory growth
            if len(self._history) > 5000:
                self._history = self._history[-5000:]

    def get_history(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Return usage history entries (newest first)."""
        with self._lock:
            entries = list(reversed(self._history))
        return [
            {
                "id": e.id,
                "timestamp": e.timestamp,
                "adapter_id": e.adapter_id,
                "model": e.model,
                "provider": e.provider,
                "transport": e.transport,
                "input_tokens": e.input_tokens,
                "output_tokens": e.output_tokens,
                "total_tokens": e.input_tokens + e.output_tokens,
                "duration_ms": e.duration_ms,
                "estimated_cost": _estimate_cost(e.model, e.input_tokens, e.output_tokens),
                "success": e.success,
                "error": e.error,
            }
            for e in entries[offset:offset + limit]
        ]

    def get_stats(self) -> dict[str, Any]:
        """Return aggregated usage statistics."""
        with self._lock:
            total_calls = len(self._history)
            if total_calls == 0:
                return {
                    "total_calls": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_duration_ms": 0,
                    "total_estimated_cost": 0.0,
                    "success_rate": 1.0,
                    "by_provider": {},
                    "by_model": {},
                    "by_hour": {},
                    "recent_calls_24h": 0,
                }
            now = time.time()
            total_input = sum(e.input_tokens for e in self._history)
            total_output = sum(e.output_tokens for e in self._history)
            total_duration = sum(e.duration_ms for e in self._history)
            successes = sum(1 for e in self._history if e.success)
            recent = sum(1 for e in self._history if now - e.timestamp < 86400)

            total_cost = sum(_estimate_cost(e.model, e.input_tokens, e.output_tokens) for e in self._history)

            by_provider: dict[str, dict] = {}
            by_model: dict[str, dict] = {}
            for e in self._history:
                p = by_provider.setdefault(e.provider, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "estimated_cost": 0.0, "errors": 0})
                p["calls"] += 1
                p["input_tokens"] += e.input_tokens
                p["output_tokens"] += e.output_tokens
                p["estimated_cost"] += _estimate_cost(e.model, e.input_tokens, e.output_tokens)
                p["errors"] += 0 if e.success else 1

                m = by_model.setdefault(e.model, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "estimated_cost": 0.0, "errors": 0})
                m["calls"] += 1
                m["input_tokens"] += e.input_tokens
                m["output_tokens"] += e.output_tokens
                m["estimated_cost"] += _estimate_cost(e.model, e.input_tokens, e.output_tokens)
                m["errors"] += 0 if e.success else 1

            return {
                "total_calls": total_calls,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_duration_ms": total_duration,
                "total_estimated_cost": round(total_cost, 6),
                "success_rate": round(successes / total_calls, 4) if total_calls else 1.0,
                "by_provider": by_provider,
                "by_model": by_model,
                "recent_calls_24h": recent,
            }

    def clear_history(self) -> None:
        with self._lock:
            self._history.clear()

    def is_available(self, adapter_id: str) -> bool:
        with self._lock:
            state = self._providers.get(adapter_id)
            if not state:
                return True
            if state.rate_limited and time.time() < state.reset_at:
                return False
            if state.cooldown_until > time.time():
                return False
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
