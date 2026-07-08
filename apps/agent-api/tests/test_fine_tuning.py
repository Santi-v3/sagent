"""Tests for fine-tuning API endpoints."""
from fastapi.testclient import TestClient

from sagent_agent_api.main import app

client = TestClient(app)


def test_finetune_requirements() -> None:
    response = client.get("/models/finetune/requirements")
    assert response.status_code == 200
    data = response.json()
    assert "qlora_available" in data
    assert "recommended" in data


def test_finetune_list_jobs_empty() -> None:
    response = client.get("/models/finetune")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_finetune_start_validation() -> None:
    response = client.post("/models/finetune", json={"base_model": "", "dataset": ""})
    assert response.status_code == 422


def test_finetune_start_invalid_model() -> None:
    """Starting with a nonexistent model returns a validation error or accepted job with failure later."""
    response = client.post("/models/finetune", json={
        "base_model": "nonexistent-model-xyz",
        "dataset": '[{"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]}]',
    })
    assert response.status_code in (201, 400, 422)
