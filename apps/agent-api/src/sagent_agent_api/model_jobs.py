"""Process-local construction and shutdown for cancellable model jobs."""

from threading import Lock

from sagent_agent_api.model_integration import get_model_router
from sagent_agent_core import ModelJobService

_service: ModelJobService | None = None
_service_lock = Lock()


def get_model_job_service() -> ModelJobService:
    """Return one bounded job service bound to the cached model router."""

    global _service
    with _service_lock:
        if _service is None:
            _service = ModelJobService(get_model_router(), max_workers=1, max_jobs=100)
        return _service


def close_model_job_service() -> None:
    """Cancel active model jobs and release the single worker during API shutdown."""

    global _service
    with _service_lock:
        service = _service
        _service = None
    if service is not None:
        service.close(wait=True)
