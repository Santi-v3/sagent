"""API tests for bounded, cancellable local model jobs."""

import json
from threading import Event
from time import monotonic, sleep
from uuid import UUID, uuid4

import httpx2 as httpx
from fastapi.testclient import TestClient

import sagent_agent_api.model_jobs as model_jobs_module
from sagent_agent_api.main import app
from sagent_agent_api.model_jobs import get_model_job_service
from sagent_agent_core import (
    LoopbackEndpoint,
    LoopbackOpenAIChatAdapter,
    ModelCapability,
    ModelJobService,
    ModelJobState,
    ModelRouter,
    ModelTransport,
)

client = TestClient(app)
MODEL = "qwen3-coder-local"


class BlockingJsonStream(httpx.SyncByteStream):
    def __init__(self, content: bytes) -> None:
        self.content = content
        self.started = Event()
        self.release = Event()
        self.closed = False

    def __iter__(self):
        midpoint = len(self.content) // 2
        self.started.set()
        yield self.content[:midpoint]
        self.release.wait(2)
        if not self.closed:
            yield self.content[midpoint:]

    def close(self) -> None:
        self.closed = True
        self.release.set()


def success_payload() -> dict[str, object]:
    return {
        "model": MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Review first."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 9, "completion_tokens": 3},
    }


def job_service(handler) -> ModelJobService:
    adapter = LoopbackOpenAIChatAdapter(
        LoopbackEndpoint("http://127.0.0.1:1234/v1"),
        MODEL,
        adapter_id="local-lm-studio",
        provider="lm-studio",
        transport=httpx.MockTransport(handler),
    )
    router = ModelRouter(
        [adapter],
        {ModelCapability.CHAT: adapter.descriptor.adapter_id},
        allowed_transports=frozenset({ModelTransport.LOOPBACK_HTTP}),
        allow_non_simulated=True,
    )
    return ModelJobService(router, max_workers=1, max_jobs=10)


def wait_for_terminal(job_id: str, timeout: float = 2) -> dict[str, object]:
    deadline = monotonic() + timeout
    while monotonic() < deadline:
        response = client.get(f"/models/jobs/{job_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["state"] in {"succeeded", "failed", "cancelled"}:
            return payload
        sleep(0.01)
    raise AssertionError("Model job API did not reach a terminal state.")


def start_payload() -> dict[str, object]:
    return {
        "adapter_id": "local-lm-studio",
        "prompt": "Plan safely.",
        "capability": "chat",
        "max_output_tokens": 128,
        "confirmed": True,
    }


def test_job_api_returns_prompt_free_success_and_rejects_late_cancel() -> None:
    service = job_service(lambda request: httpx.Response(200, json=success_payload()))
    app.dependency_overrides[get_model_job_service] = lambda: service
    try:
        created = client.post("/models/jobs", json=start_payload())
        assert created.status_code == 202
        completed = wait_for_terminal(created.json()["job_id"])
        late_cancel = client.post(f"/models/jobs/{created.json()['job_id']}/cancel")
    finally:
        app.dependency_overrides.clear()
        service.close()

    assert completed["state"] == "succeeded"
    assert completed["result"]["content"] == "Review first."
    assert completed["result"]["untrusted"] is True
    assert completed["result"]["simulated"] is False
    assert "Plan safely" not in json.dumps(completed)
    assert late_cancel.status_code == 409


def test_running_job_is_actively_cancelled_and_response_closed() -> None:
    stream = BlockingJsonStream(json.dumps(success_payload()).encode("utf-8"))
    service = job_service(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "application/json"},
            stream=stream,
        )
    )
    app.dependency_overrides[get_model_job_service] = lambda: service
    try:
        created = client.post("/models/jobs", json=start_payload())
        assert created.status_code == 202
        assert stream.started.wait(1)

        cancelling = client.post(f"/models/jobs/{created.json()['job_id']}/cancel")
        completed = wait_for_terminal(created.json()["job_id"])
    finally:
        app.dependency_overrides.clear()
        service.close()

    assert cancelling.status_code == 200
    assert cancelling.json()["state"] in {"cancelling", "cancelled"}
    assert completed["state"] == "cancelled"
    assert completed["result"] is None
    assert completed["error"] is None
    assert stream.closed is True


def test_job_failure_is_generic_and_provider_details_stay_hidden() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("provider-sensitive-timeout")

    service = job_service(handler)
    app.dependency_overrides[get_model_job_service] = lambda: service
    try:
        created = client.post("/models/jobs", json=start_payload())
        completed = wait_for_terminal(created.json()["job_id"])
    finally:
        app.dependency_overrides.clear()
        service.close()

    assert completed["state"] == "failed"
    assert completed["error"] == "Local model job failed safely."
    assert "provider" not in completed["error"]


def test_job_api_requires_confirmation_known_adapter_and_known_job() -> None:
    service = job_service(lambda request: httpx.Response(200, json=success_payload()))
    app.dependency_overrides[get_model_job_service] = lambda: service
    try:
        missing_confirmation_payload = start_payload()
        missing_confirmation_payload["confirmed"] = False
        missing_confirmation = client.post(
            "/models/jobs",
            json=missing_confirmation_payload,
        )
        unknown_adapter_payload = start_payload()
        unknown_adapter_payload["adapter_id"] = "local-missing"
        unknown_adapter = client.post("/models/jobs", json=unknown_adapter_payload)
        missing_job = client.get(f"/models/jobs/{uuid4()}")
        missing_cancel = client.post(f"/models/jobs/{uuid4()}/cancel")
    finally:
        app.dependency_overrides.clear()
        service.close()

    assert missing_confirmation.status_code == 422
    assert unknown_adapter.status_code == 422
    assert missing_job.status_code == 404
    assert missing_cancel.status_code == 404


def test_api_shutdown_cancels_active_job_and_closes_response_stream() -> None:
    stream = BlockingJsonStream(json.dumps(success_payload()).encode("utf-8"))
    service = job_service(
        lambda request: httpx.Response(
            200,
            headers={"content-type": "application/json"},
            stream=stream,
        )
    )
    model_jobs_module._service = service
    try:
        with TestClient(app) as lifecycle_client:
            created = lifecycle_client.post("/models/jobs", json=start_payload())
            assert created.status_code == 202
            assert stream.started.wait(1)

        snapshot = service.get(UUID(created.json()["job_id"]))

        assert snapshot.state is ModelJobState.CANCELLED
        assert stream.closed is True
        assert model_jobs_module._service is None
        model_jobs_module.close_model_job_service()
    finally:
        model_jobs_module.close_model_job_service()
