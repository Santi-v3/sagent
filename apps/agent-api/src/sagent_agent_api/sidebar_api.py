"""REST API for sidebar conversations, projects, and account data.

Data is persisted to ~/.sagent/sidebar.json so it survives restarts.
"""

from __future__ import annotations

import json
import time
import uuid as uuid_mod
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from sagent_agent_api.models import (
    SidebarAccountResponse,
    SidebarConversationCreate,
    SidebarConversationResponse,
    SidebarConversationUpdate,
    SidebarDataResponse,
    SidebarProjectCreate,
    SidebarProjectResponse,
    SidebarProjectUpdate,
)

_DATA_DIR = Path.home() / ".sagent"
_DATA_PATH = _DATA_DIR / "sidebar.json"

router = APIRouter(prefix="/sidebar", tags=["sidebar"])


class SidebarService:
    """Manages sidebar state in a JSON file."""

    def __init__(self) -> None:
        self._data: dict = {}
        self._load()

    # ── persistence ──

    def _load(self) -> None:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        if _DATA_PATH.exists():
            try:
                self._data = json.loads(_DATA_PATH.read_text())
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}
        self._migrate()

    def _save(self) -> None:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        _DATA_PATH.write_text(json.dumps(self._data, indent=2))

    def _migrate(self) -> None:
        changed = False
        if "conversations" not in self._data:
            self._data["conversations"] = []
            changed = True
        if "projects" not in self._data:
            self._data["projects"] = []
            changed = True
        if "account" not in self._data or not self._data["account"].get("menuItems"):
            self._data["account"] = {"name": "User", "plan": "Pilot", "menuItems": [{"id": "tools", "label": "Werkzeuge"}, {"id": "settings", "label": "Einstellungen"}, {"id": "logout", "label": "Abmelden", "danger": True}]}
            changed = True
        if changed:
            self._save()

    # ── conversations ──

    def get_conversations(self) -> list[dict]:
        return list(self._data["conversations"])

    def get_conversation(self, conv_id: str) -> dict | None:
        for c in self._data["conversations"]:
            if c["id"] == conv_id:
                return dict(c)
        return None

    def create_conversation(self, payload: SidebarConversationCreate) -> dict:
        conv = {
            "id": uuid_mod.uuid4().hex[:12],
            "label": payload.label or "Neue Konversation",
            "messages": [m.model_dump() for m in payload.messages],
            "updatedAt": time.time(),
            "pinned": False,
            "projectId": payload.projectId,
        }
        self._data["conversations"].insert(0, conv)
        self._save()
        return dict(conv)

    def update_conversation(self, conv_id: str, payload: SidebarConversationUpdate) -> dict:
        for c in self._data["conversations"]:
            if c["id"] == conv_id:
                if payload.label is not None:
                    c["label"] = payload.label
                if payload.pinned is not None:
                    c["pinned"] = payload.pinned
                if payload.projectId is not None:
                    c["projectId"] = payload.projectId
                if payload.messages is not None:
                    c["messages"] = [m.model_dump() for m in payload.messages]
                c["updatedAt"] = time.time()
                self._save()
                return dict(c)
        raise HTTPException(status_code=404, detail="Conversation not found")

    def delete_conversation(self, conv_id: str) -> None:
        before = len(self._data["conversations"])
        self._data["conversations"] = [c for c in self._data["conversations"] if c["id"] != conv_id]
        if len(self._data["conversations"]) == before:
            raise HTTPException(status_code=404, detail="Conversation not found")
        self._save()

    # ── projects ──

    def get_projects(self) -> list[dict]:
        return list(self._data["projects"])

    def create_project(self, payload: SidebarProjectCreate) -> dict:
        project = {
            "id": uuid_mod.uuid4().hex[:12],
            "name": payload.name,
            "createdAt": time.time(),
        }
        self._data["projects"].append(project)
        self._save()
        return dict(project)

    def update_project(self, project_id: str, payload: SidebarProjectUpdate) -> dict:
        for p in self._data["projects"]:
            if p["id"] == project_id:
                if payload.name is not None:
                    p["name"] = payload.name
                self._save()
                return dict(p)
        raise HTTPException(status_code=404, detail="Project not found")

    def delete_project(self, project_id: str) -> None:
        before = len(self._data["projects"])
        self._data["projects"] = [p for p in self._data["projects"] if p["id"] != project_id]
        if len(self._data["projects"]) == before:
            raise HTTPException(status_code=404, detail="Project not found")
        # unlink conversations from deleted project
        for c in self._data["conversations"]:
            if c.get("projectId") == project_id:
                c["projectId"] = None
        self._save()

    # ── account ──

    def get_account(self) -> dict:
        return dict(self._data["account"])


# ── singleton ──

_service: SidebarService | None = None


def get_sidebar_service() -> SidebarService:
    global _service
    if _service is None:
        _service = SidebarService()
    return _service


SidebarServiceDependency = Annotated[SidebarService, Depends(get_sidebar_service)]


# ── routes ──


@router.get("/data", response_model=SidebarDataResponse)
def get_sidebar_data(service: SidebarServiceDependency) -> SidebarDataResponse:
    """Return all sidebar state in one round-trip."""
    return SidebarDataResponse(
        conversations=[SidebarConversationResponse(**c) for c in service.get_conversations()],
        projects=[SidebarProjectResponse(**p) for p in service.get_projects()],
        account=SidebarAccountResponse(**service.get_account()),
    )


@router.get("/conversations", response_model=list[SidebarConversationResponse])
def list_conversations(service: SidebarServiceDependency) -> list[SidebarConversationResponse]:
    return [SidebarConversationResponse(**c) for c in service.get_conversations()]


@router.get("/conversations/{conv_id}", response_model=SidebarConversationResponse)
def get_conversation(
    conv_id: str, service: SidebarServiceDependency
) -> SidebarConversationResponse:
    c = service.get_conversation(conv_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return SidebarConversationResponse(**c)


@router.post("/conversations", response_model=SidebarConversationResponse, status_code=201)
def create_conversation(
    payload: SidebarConversationCreate, service: SidebarServiceDependency
) -> SidebarConversationResponse:
    return SidebarConversationResponse(**service.create_conversation(payload))


@router.patch("/conversations/{conv_id}", response_model=SidebarConversationResponse)
def update_conversation(
    conv_id: str, payload: SidebarConversationUpdate, service: SidebarServiceDependency
) -> SidebarConversationResponse:
    return SidebarConversationResponse(**service.update_conversation(conv_id, payload))


@router.delete("/conversations/{conv_id}", status_code=204)
def delete_conversation(conv_id: str, service: SidebarServiceDependency):
    service.delete_conversation(conv_id)


@router.get("/projects", response_model=list[SidebarProjectResponse])
def list_projects(service: SidebarServiceDependency) -> list[SidebarProjectResponse]:
    return [SidebarProjectResponse(**p) for p in service.get_projects()]


@router.post("/projects", response_model=SidebarProjectResponse, status_code=201)
def create_project(
    payload: SidebarProjectCreate, service: SidebarServiceDependency
) -> SidebarProjectResponse:
    return SidebarProjectResponse(**service.create_project(payload))


@router.patch("/projects/{project_id}", response_model=SidebarProjectResponse)
def update_project(
    project_id: str, payload: SidebarProjectUpdate, service: SidebarServiceDependency
) -> SidebarProjectResponse:
    return SidebarProjectResponse(**service.update_project(project_id, payload))


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str, service: SidebarServiceDependency):
    service.delete_project(project_id)


@router.get("/account", response_model=SidebarAccountResponse)
def get_account(service: SidebarServiceDependency) -> SidebarAccountResponse:
    return SidebarAccountResponse(**service.get_account())
