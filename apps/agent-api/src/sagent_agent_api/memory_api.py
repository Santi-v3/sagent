
from typing import Annotated

from fastapi import Depends
from sagent_memory import MemoryService

_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    global _service
    if _service is None:
        _service = MemoryService()
    return _service


def close_memory_service() -> None:
    global _service
    if _service is not None:
        _service.clear()
        _service = None


MemoryServiceDependency = Annotated[MemoryService, Depends(get_memory_service)]
