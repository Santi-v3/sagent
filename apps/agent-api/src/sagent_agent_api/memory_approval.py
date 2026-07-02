"""Process-local, hash-bound approval flow for local memory writes."""

import hashlib
import hmac
import json
from dataclasses import dataclass
from functools import lru_cache
from threading import Lock
from types import MappingProxyType
from uuid import UUID, uuid4

from sagent_memory import MemoryContractError, MemoryEntry, MemoryService, MetadataValue

from sagent_tools import redact_secrets


class MemoryProposalError(ValueError):
    pass


class MemoryProposalNotFoundError(KeyError):
    pass


class MemoryProposalConflictError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class MemoryProposal:
    proposal_id: UUID
    text: str
    metadata: dict[str, MetadataValue]
    proposal_hash: str
    status: str


class MemoryApprovalService:
    def __init__(self, memory: MemoryService | None = None) -> None:
        self.memory = memory or MemoryService()
        self._proposals: dict[UUID, MemoryProposal] = {}
        self._lock = Lock()

    def preview(
        self, text: str, metadata: dict[str, MetadataValue] | None = None
    ) -> MemoryProposal:
        normalized = text.strip()
        if not normalized:
            raise MemoryProposalError("Memory text must contain visible characters.")
        if redact_secrets(normalized)[1]:
            raise MemoryProposalError("Potential secret content blocks this memory proposal.")
        values = dict(metadata or {})
        validated = self.memory.validate_metadata(values)
        metadata_scan = "\n".join(f"{key}={value}" for key, value in validated.items())
        if redact_secrets(metadata_scan)[1]:
            raise MemoryProposalError("Potential secret metadata blocks this memory proposal.")
        proposal_id = uuid4()
        canonical = json.dumps(
            {"proposal_id": str(proposal_id), "text": normalized, "metadata": validated},
            sort_keys=True,
            separators=(",", ":"),
        )
        proposal = MemoryProposal(
            proposal_id=proposal_id,
            text=normalized,
            metadata=MappingProxyType(validated),  # type: ignore[arg-type]
            proposal_hash=hashlib.sha256(canonical.encode()).hexdigest(),
            status="prepared",
        )
        with self._lock:
            self._proposals[proposal_id] = proposal
        return proposal

    def _get(self, proposal_id: UUID) -> MemoryProposal:
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            raise MemoryProposalNotFoundError("Memory proposal not found.")
        return proposal

    def approve(self, proposal_id: UUID, proposal_hash: str) -> MemoryProposal:
        with self._lock:
            proposal = self._get(proposal_id)
            if proposal.status != "prepared":
                raise MemoryProposalConflictError("Memory proposal is not pending approval.")
            if not hmac.compare_digest(proposal.proposal_hash, proposal_hash):
                raise MemoryProposalConflictError("Memory proposal hash does not match.")
            approved = MemoryProposal(
                proposal.proposal_id,
                proposal.text,
                proposal.metadata,
                proposal.proposal_hash,
                "approved",
            )
            self._proposals[proposal_id] = approved
            return approved

    def apply(self, proposal_id: UUID, proposal_hash: str) -> tuple[MemoryProposal, MemoryEntry]:
        with self._lock:
            proposal = self._get(proposal_id)
            if proposal.status != "approved":
                raise MemoryProposalConflictError("Memory proposal is not approved.")
            if not hmac.compare_digest(proposal.proposal_hash, proposal_hash):
                raise MemoryProposalConflictError("Memory proposal hash does not match.")
            try:
                entry = self.memory.store(proposal.text, proposal.metadata, confirmed=True)
            except MemoryContractError as error:
                raise MemoryProposalConflictError(str(error)) from error
            applied = MemoryProposal(
                proposal.proposal_id,
                proposal.text,
                proposal.metadata,
                proposal.proposal_hash,
                "applied",
            )
            self._proposals[proposal_id] = applied
            return applied, entry


@lru_cache(maxsize=1)
def get_memory_approval_service() -> MemoryApprovalService:
    return MemoryApprovalService()
