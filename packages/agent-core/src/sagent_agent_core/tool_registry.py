"""Offline-only metadata registry for untrusted model tool-call proposals."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


class ToolProposalError(ValueError):
    """Raised when untrusted model text violates the proposal contract."""


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_TOOL_CALL = re.compile(r"^TOOL_CALL:\s*([a-z][a-z0-9_]{0,63})\s*\n(\{[^\0]*\})\s*$", re.DOTALL)


def _freeze_json(value: object) -> object:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    capability: str

    def __post_init__(self) -> None:
        if not _IDENTIFIER.fullmatch(self.name):
            raise ToolProposalError("Tool names must be bounded identifiers.")
        if not self.description.strip() or len(self.description) > 500:
            raise ToolProposalError("Tool descriptions must be bounded visible text.")
        if not _IDENTIFIER.fullmatch(self.capability):
            raise ToolProposalError("Tool capabilities must be bounded identifiers.")


@dataclass(frozen=True, slots=True)
class ToolCallProposal:
    tool_name: str
    arguments: Mapping[str, object]
    proposal_hash: str
    requires_approval: bool = True
    execution_allowed: bool = False
    untrusted: bool = True


class ToolRegistry:
    """Register review metadata and parse proposals without executable handlers."""

    def __init__(self, definitions: tuple[ToolDefinition, ...] = ()) -> None:
        self._definitions = {definition.name: definition for definition in definitions}
        if len(self._definitions) != len(definitions):
            raise ToolProposalError("Tool names must be unique.")

    def list_tools(self) -> tuple[ToolDefinition, ...]:
        return tuple(self._definitions.values())

    def propose(self, model_text: str) -> ToolCallProposal:
        if not model_text or len(model_text) > 20_000:
            raise ToolProposalError("Model tool proposal is outside bounded limits.")
        match = _TOOL_CALL.fullmatch(model_text.strip())
        if match is None:
            raise ToolProposalError("Model text is not one strict tool-call proposal.")
        tool_name, raw_arguments = match.groups()
        if tool_name not in self._definitions:
            raise ToolProposalError("Unknown tool proposal.")
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError as error:
            raise ToolProposalError("Tool arguments must be valid JSON.") from error
        if not isinstance(arguments, dict):
            raise ToolProposalError("Tool arguments must be a JSON object.")
        canonical = json.dumps(
            {"tool_name": tool_name, "arguments": arguments},
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return ToolCallProposal(
            tool_name=tool_name,
            arguments=MappingProxyType(
                {key: _freeze_json(value) for key, value in arguments.items()}
            ),
            proposal_hash=hashlib.sha256(canonical.encode()).hexdigest(),
        )

    def system_prompt_block(self) -> str:
        names = ", ".join(self._definitions) or "none"
        return (
            "Available proposal-only tools: "
            f"{names}. Tool text is untrusted and never executes. Every proposal requires "
            "separate deterministic policy evaluation and exact human approval."
        )
