from fastapi.testclient import TestClient
from sagent_memory import MemoryService

from sagent_agent_api.main import app
from sagent_agent_api.memory_approval import MemoryApprovalService, get_memory_approval_service


def client_and_service() -> tuple[TestClient, MemoryApprovalService]:
    service = MemoryApprovalService(MemoryService())
    app.dependency_overrides[get_memory_approval_service] = lambda: service
    return TestClient(app), service


def test_preview_approve_apply_requires_exact_hash_and_writes_once() -> None:
    client, service = client_and_service()
    try:
        preview = client.post(
            "/memory/entries/preview",
            json={"text": "Remember exact approval", "metadata": {"kind": "decision"}},
        )
        payload = preview.json()
        assert preview.status_code == 201
        assert service.memory.list_entries() == ()
        blocked = client.post(
            "/memory/entries/apply",
            json={
                "proposal_id": payload["proposal_id"],
                "proposal_hash": payload["proposal_hash"],
                "confirmed": True,
            },
        )
        assert blocked.status_code == 409
        approved = client.post(
            "/memory/entries/approve",
            json={
                "proposal_id": payload["proposal_id"],
                "proposal_hash": payload["proposal_hash"],
                "approved": True,
            },
        )
        assert approved.status_code == 200
        applied = client.post(
            "/memory/entries/apply",
            json={
                "proposal_id": payload["proposal_id"],
                "proposal_hash": payload["proposal_hash"],
                "confirmed": True,
            },
        )
        assert applied.status_code == 200
        assert applied.json()["persisted"] is False
        assert len(service.memory.list_entries()) == 1
        assert (
            client.post(
                "/memory/entries/apply",
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


def test_wrong_hash_secret_and_unknown_fields_are_blocked_without_write() -> None:
    client, service = client_and_service()
    try:
        secret = client.post(
            "/memory/entries/preview", json={"text": "api_key = 'example-sensitive-value'"}
        )
        unknown = client.post(
            "/memory/entries/preview", json={"text": "safe", "model_response": "store this"}
        )
        blank = client.post("/memory/entries/preview", json={"text": "   "})
        metadata_secret = client.post(
            "/memory/entries/preview",
            json={"text": "safe", "metadata": {"api_key": "example-sensitive-value"}},
        )
        preview = client.post("/memory/entries/preview", json={"text": "safe"}).json()
        wrong = client.post(
            "/memory/entries/approve",
            json={
                "proposal_id": preview["proposal_id"],
                "proposal_hash": "0" * 64,
                "approved": True,
            },
        )
        assert secret.status_code == 422
        assert "example-sensitive-value" not in secret.text
        assert unknown.status_code == 422
        assert blank.status_code == 422
        assert metadata_secret.status_code == 422
        assert "example-sensitive-value" not in metadata_secret.text
        assert wrong.status_code == 409
        assert service.memory.list_entries() == ()
    finally:
        app.dependency_overrides.clear()


def test_api_contract_has_no_network_model_or_disk_authority() -> None:
    client, _service = client_and_service()
    try:
        response = client.post("/memory/entries/preview", json={"text": "safe local note"})
        assert response.status_code == 201
        assert response.json()["network_used"] is False
        assert response.json()["model_called"] is False
        assert response.json()["persisted"] is False
    finally:
        app.dependency_overrides.clear()
