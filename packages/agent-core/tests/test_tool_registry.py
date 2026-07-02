from dataclasses import FrozenInstanceError

import pytest

from sagent_agent_core.tool_registry import ToolDefinition, ToolProposalError, ToolRegistry


def registry() -> ToolRegistry:
    definition = ToolDefinition("read_file", "Preview one local file read.", "read_files")
    return ToolRegistry((definition,))


def test_model_text_creates_untrusted_non_executable_proposal() -> None:
    proposal = registry().propose('TOOL_CALL: read_file\n{"path":"README.md"}')

    assert proposal.tool_name == "read_file"
    assert dict(proposal.arguments) == {"path": "README.md"}
    assert proposal.requires_approval is True
    assert proposal.execution_allowed is False
    assert proposal.untrusted is True
    assert len(proposal.proposal_hash) == 64


def test_proposal_hash_is_stable_and_content_bound() -> None:
    first = registry().propose('TOOL_CALL: read_file\n{"path":"README.md"}')
    same = registry().propose('TOOL_CALL: read_file\n{"path": "README.md"}')
    changed = registry().propose('TOOL_CALL: read_file\n{"path":"docs/SECURITY.md"}')

    assert first.proposal_hash == same.proposal_hash
    assert first.proposal_hash != changed.proposal_hash


@pytest.mark.parametrize(
    "text",
    [
        "normal model answer",
        'TOOL_CALL: unknown\n{"path":"README.md"}',
        "TOOL_CALL: read_file\nnot-json",
        'prefix\nTOOL_CALL: read_file\n{"path":"README.md"}',
    ],
)
def test_invalid_or_unknown_model_tool_text_is_rejected(text: str) -> None:
    with pytest.raises(ToolProposalError):
        registry().propose(text)


def test_registry_has_no_handler_or_dispatch_surface() -> None:
    tool = registry().list_tools()[0]

    assert not hasattr(tool, "handler")
    assert not hasattr(registry(), "dispatch")
    with pytest.raises(FrozenInstanceError):
        tool.name = "write_file"  # type: ignore[misc]


def test_nested_proposal_arguments_are_immutable() -> None:
    proposal = registry().propose(
        'TOOL_CALL: read_file\n{"options":{"paths":["README.md"]}}'
    )

    nested = proposal.arguments["options"]
    assert isinstance(nested, dict) is False
    with pytest.raises(TypeError):
        nested["paths"] = ()  # type: ignore[index]
