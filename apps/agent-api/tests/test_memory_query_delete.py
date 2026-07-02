from fastapi.testclient import TestClient
from sagent_memory import MemoryService

from sagent_agent_api.main import app
from sagent_agent_api.memory_approval import MemoryApprovalService, get_memory_approval_service


def setup_client() -> tuple[TestClient, MemoryApprovalService, str]:
    service = MemoryApprovalService(MemoryService())
    entry = service.memory.store(
        "Sagent approval decisions are local",
        {"kind": "decision"},
        confirmed=True,
    )
    app.dependency_overrides[get_memory_approval_service] = lambda: service
    return TestClient(app), service, entry.entry_id


def test_list_and_search_are_read_only_offline_and_untrusted() -> None:
    client, service, entry_id = setup_client()
    try:
        listed = client.get("/memory/entries")
        searched = client.post("/memory/search", json={"query": "approval", "limit": 5})

        assert listed.status_code == 200
        assert searched.status_code == 200
        assert listed.json()[0]["entry_id"] == entry_id
        assert searched.json()[0]["score"] > 0
        assert searched.json()[0]["untrusted"] is True
        assert searched.json()[0]["network_used"] is False
        assert searched.json()[0]["model_called"] is False
        assert len(service.memory.list_entries()) == 1
    finally:
        app.dependency_overrides.clear()


def test_search_rejects_unknown_fields_and_blank_query() -> None:
    client, _service, _entry_id = setup_client()
    try:
        unknown = client.post("/memory/search", json={"query": "safe", "model_response": "x"})
        blank = client.post("/memory/search", json={"query": "   "})

        assert unknown.status_code == 422
        assert blank.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_delete_requires_exact_approval_and_is_single_use() -> None:
    client, service, entry_id = setup_client()
    try:
        preview = client.post("/memory/deletions/preview", json={"entry_id": entry_id})
        payload = preview.json()
        assert preview.status_code == 201
        assert service.memory.get(entry_id) is not None

        unapproved = client.post(
            "/memory/deletions/apply",
            json={
                "proposal_id": payload["proposal_id"],
                "proposal_hash": payload["proposal_hash"],
                "confirmed": True,
            },
        )
        assert unapproved.status_code == 409
        approved = client.post(
            "/memory/deletions/approve",
            json={
                "proposal_id": payload["proposal_id"],
                "proposal_hash": payload["proposal_hash"],
                "approved": True,
            },
        )
        assert approved.status_code == 200
        applied = client.post(
            "/memory/deletions/apply",
            json={
                "proposal_id": payload["proposal_id"],
                "proposal_hash": payload["proposal_hash"],
                "confirmed": True,
            },
        )
        assert applied.status_code == 200
        assert service.memory.get(entry_id) is None
        assert (
            client.post(
                "/memory/deletions/apply",
                json={
                    "proposal_id": payload["proposal_id"],
                    "proposal_hash": payload["proposal_hash"],
                    "confirmed": True,
                },
            ).status_code
            == 409
        )
    finally:
        app.dependency_overrides.clear()


def test_delete_unknown_entry_and_wrong_hash_are_blocked() -> None:
    client, service, entry_id = setup_client()
    try:
        missing = client.post("/memory/deletions/preview", json={"entry_id": "0" * 32})
        preview = client.post("/memory/deletions/preview", json={"entry_id": entry_id}).json()
        wrong = client.post(
            "/memory/deletions/approve",
            json={
                "proposal_id": preview["proposal_id"],
                "proposal_hash": "0" * 64,
                "approved": True,
            },
        )
        assert missing.status_code == 404
        assert wrong.status_code == 409
        assert service.memory.get(entry_id) is not None
    finally:
        app.dependency_overrides.clear()
