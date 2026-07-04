"use client";

import { CaretRight, DotsThreeVertical, Folder, Plus } from "@phosphor-icons/react";
import { useState } from "react";
import { ChatRow } from "./chat-row";
import type { SidebarConversation, SidebarProject } from "./types";

export type ProjectsSectionProps = {
  projects: SidebarProject[];
  conversations: SidebarConversation[];
  activeConvId: string | null;
  collapsedProjectIds: Set<string>;
  searchQuery: string;
  onCreateProject: (name: string) => void;
  onToggleCollapsed: (id: string) => void;
  onSelectConversation: (id: string) => void;
  onConversationContextMenu: (e: React.MouseEvent, convId: string) => void;
  onRequestConversationContextMenu: (rect: DOMRect, convId: string) => void;
  onProjectContextMenu: (e: React.MouseEvent, projectId: string) => void;
  onRequestProjectContextMenu: (rect: DOMRect, projectId: string) => void;
  onRenameProjectRequest: (projectId: string) => void;
  onRenameConversationSubmit: (id: string, label: string) => void;
};

export function ProjectsSection(props: ProjectsSectionProps) {
  const {
    projects, conversations, activeConvId, collapsedProjectIds, searchQuery,
    onCreateProject, onToggleCollapsed,
    onSelectConversation, onConversationContextMenu, onRequestConversationContextMenu,
    onProjectContextMenu, onRequestProjectContextMenu, onRenameProjectRequest,
    onRenameConversationSubmit,
  } = props;

  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState("");

  function submitCreate(ev: React.FormEvent) {
    ev.preventDefault();
    const name = newName.trim();
    if (!name) return;
    onCreateProject(name);
    setNewName("");
    setCreateOpen(false);
  }

  if (projects.length === 0 && !searchQuery) {
    return (
      <section className="sidebar-section sidebar-project-section" aria-label="Projekte">
        <div className="sidebar-section-heading">
          <span className="sidebar-section-title">Projekte</span>
          <button
            type="button"
            className="sidebar-projects-add"
            aria-label="Projekt erstellen"
            title="Projekt erstellen"
            onClick={() => setCreateOpen((v) => !v)}
          >
            <Plus weight="bold" aria-hidden="true" />
          </button>
        </div>
        {createOpen && (
          <form className="sidebar-project-create" onSubmit={submitCreate}>
            <input
              type="text"
              className="conv-rename-input"
              placeholder="Projektname…"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Escape") {
                  setCreateOpen(false);
                  setNewName("");
                }
              }}
            />
          </form>
        )}
      </section>
    );
  }

  return (
    <section className="sidebar-section sidebar-project-section" aria-label="Projekte">
        <div className="sidebar-section-heading">
        <span className="sidebar-section-title">Projekte</span>
        <button
          type="button"
          className="sidebar-projects-add"
          aria-label="Projekt erstellen"
          title="Projekt erstellen"
          onClick={() => setCreateOpen((v) => !v)}
        >
          <Plus weight="bold" aria-hidden="true" />
        </button>
      </div>
      {createOpen && (
        <form className="sidebar-project-create" onSubmit={submitCreate}>
          <input
            type="text"
            className="conv-rename-input"
            placeholder="Projektname…"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            autoFocus
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                setCreateOpen(false);
                setNewName("");
              }
            }}
          />
        </form>
      )}
      {projects.map((project) => {
        const projectConvs = conversations.filter(
          (c) => c.projectId === project.id
            && (!searchQuery || c.label.toLowerCase().includes(searchQuery.toLowerCase()))
        );
        const isCollapsed = collapsedProjectIds.has(project.id);
        const hasAnyConv = conversations.some((c) => c.projectId === project.id);
        return (
          <div key={project.id} className="project-section">
            <button
              type="button"
              className="project-toggle"
              onClick={() => onToggleCollapsed(project.id)}
              onContextMenu={(e) => onProjectContextMenu(e, project.id)}
            >
              <CaretRight
                className={`sidebar-toggle-arrow${isCollapsed ? "" : " open"}`}
                weight="bold"
                aria-hidden="true"
              />
              <Folder className="project-folder-icon" weight="regular" aria-hidden="true" />
              <span className="project-name">{project.name}</span>
              <span
                role="button"
                tabIndex={0}
                className="project-burger"
                aria-label="Projekt-Aktionen"
                title="Projekt-Aktionen"
                onClick={(e) => {
                  e.stopPropagation();
                  onRequestProjectContextMenu(
                    (e.currentTarget as HTMLSpanElement).getBoundingClientRect(),
                    project.id
                  );
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    e.stopPropagation();
                    onRenameProjectRequest(project.id);
                  }
                }}
              >
                <DotsThreeVertical weight="bold" aria-hidden="true" />
              </span>
            </button>
            {!isCollapsed && projectConvs.length > 0 && projectConvs.map((c) => (
              <ChatRow
                key={c.id}
                conv={c}
                active={c.id === activeConvId}
                indented
                onSelect={() => onSelectConversation(c.id)}
                onContextMenu={(e) => onConversationContextMenu(e, c.id)}
                onRequestContextMenu={(rect) => onRequestConversationContextMenu(rect, c.id)}
                onRenameSubmit={(label) => onRenameConversationSubmit(c.id, label)}
              />
            ))}
            {!isCollapsed && projectConvs.length === 0 && (
              <div className="project-empty">{hasAnyConv ? "Keine Treffer" : "Keine Chats"}</div>
            )}
          </div>
        );
      })}
    </section>
  );
}
