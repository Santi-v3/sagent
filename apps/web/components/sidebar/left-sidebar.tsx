"use client";

import { useEffect, useMemo, useState } from "react";
import { SidebarTop } from "./sidebar-top";
import { PrimaryNav } from "./primary-nav";
import { ProjectsSection } from "./projects-section";
import { ChatsSection } from "./chats-section";
import {
  ConversationContextMenu,
  ProjectContextMenu,
} from "./context-menu";
import { SearchModal } from "./search-modal";
import { ConfirmDialog } from "./confirm-dialog";
import { AccountFooter } from "./account-footer";
import {
  loadCollapsed,
  loadSidebarWidth,
  persistCollapsed,
  persistSidebarWidth,
} from "./utils";
import type { LeftSidebarProps, SidebarConversation, SidebarProject } from "./types";

type View = "chats" | "planned" | "plugins";

type ConvContextState = { position: { x: number; y: number } | null; convId: string | null };
type ProjectContextState = { position: { x: number; y: number } | null; projectId: string | null };

type PendingDelete =
  | { kind: "conversation"; conv: SidebarConversation }
  | { kind: "project"; project: SidebarProject; convCount: number };

type PendingRename =
  | { kind: "conversation"; convId: string; current: string }
  | { kind: "project"; projectId: string; current: string }
  | null;

export function LeftSidebar(props: LeftSidebarProps & { className?: string }) {
  const {
    conversations, projects, activeConvId,
    onSelectConversation, onNewChat,
    onDeleteConversation, onRenameConversation, onTogglePinConversation,
    onAssignConversationToProject,
    onCreateProject, onDeleteProject, onRenameProject,
    onOpenSettings, onOpenSearch,
    onSelectProject,
    account, initialCollapsed = false,
    className = "",
  } = props;

  const [hydrated, setHydrated] = useState(false);
  const [collapsed, setCollapsed] = useState<boolean>(initialCollapsed);
  const [sidebarWidth, setSidebarWidth] = useState<number>(320);
  const [isResizing, setIsResizing] = useState(false);
  const [collapsedProjectIds, setCollapsedProjectIds] = useState<Set<string>>(new Set());
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [view, setView] = useState<View>("chats");
  const [convCtx, setConvCtx] = useState<ConvContextState>({ position: null, convId: null });
  const [projectCtx, setProjectCtx] = useState<ProjectContextState>({ position: null, projectId: null });
  const [pendingDelete, setPendingDelete] = useState<PendingDelete | null>(null);
  const [pendingRename, setPendingRename] = useState<PendingRename>(null);
  const [renameDraft, setRenameDraft] = useState("");

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- hydration from localStorage
    setCollapsed(loadCollapsed(initialCollapsed));
    setSidebarWidth(loadSidebarWidth(320));
    setHydrated(true);
  }, [initialCollapsed]);

  useEffect(() => { if (hydrated) persistCollapsed(collapsed); }, [collapsed, hydrated]);
  useEffect(() => { if (hydrated) persistSidebarWidth(sidebarWidth); }, [sidebarWidth, hydrated]);

  const filteredConversations = useMemo(() => conversations, [conversations]);

  const MIN_SIDEBAR = 240;
  const MAX_SIDEBAR = 320;

  function handleResizeStart(e: React.MouseEvent) {
    e.preventDefault();
    setIsResizing(true);
    const startX = e.clientX;
    const startWidth = sidebarWidth;
    function onMove(ev: MouseEvent) {
      const w = Math.max(MIN_SIDEBAR, Math.min(MAX_SIDEBAR, startWidth + ev.clientX - startX));
      setSidebarWidth(w);
    }
    function onUp() {
      setIsResizing(false);
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    }
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }

  function toggleProjectCollapsed(id: string) {
    setCollapsedProjectIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function startRenameConv(conv: SidebarConversation) {
    setRenameDraft(conv.label);
    setPendingRename({ kind: "conversation", convId: conv.id, current: conv.label });
  }

  function startRenameProject(project: SidebarProject) {
    setRenameDraft(project.name);
    setPendingRename({ kind: "project", projectId: project.id, current: project.name });
  }

  function commitRename() {
    if (!pendingRename) return;
    const value = renameDraft.trim();
    if (value && value !== pendingRename.current) {
      if (pendingRename.kind === "conversation") onRenameConversation(pendingRename.convId, value);
      else onRenameProject(pendingRename.projectId, value);
    }
    setPendingRename(null);
    setRenameDraft("");
  }

  const convForCtx = convCtx.convId ? conversations.find((c) => c.id === convCtx.convId) ?? null : null;
  const projectForCtx = projectCtx.projectId ? projects.find((p) => p.id === projectCtx.projectId) ?? null : null;
  const convCountForProject = (id: string) => conversations.filter((c) => c.projectId === id).length;

  return (
    <aside
      className={`sidebar${collapsed ? " sidebar--collapsed" : ""}${isResizing ? " sidebar--resizing" : ""}${className ? ` ${className}` : ""}`}
      aria-label="App-Navigation"
      style={collapsed ? undefined : { width: sidebarWidth }}
    >
      <SidebarTop
        collapsed={collapsed}
        onToggleCollapsed={() => setCollapsed((v) => !v)}
      />

      <PrimaryNav
        collapsed={collapsed}
        onNewChat={onNewChat}
        onOpenSearch={() => {
          if (view !== "chats") setView("chats");
          setSearchModalOpen(true);
          onOpenSearch();
        }}
        activeView={view}
      />

      {!collapsed && (
        <div className="sidebar-conversations">
          {view === "planned" ? (
            <div className="sidebar-view-empty">Noch nichts geplant</div>
          ) : view === "plugins" ? (
            <div className="sidebar-view-empty">Keine Plugins installiert</div>
          ) : (
            <>
              <ProjectsSection
                projects={projects}
                conversations={filteredConversations}
                activeConvId={activeConvId}
                collapsedProjectIds={collapsedProjectIds}
                searchQuery=""
                onCreateProject={onCreateProject}
                onToggleCollapsed={toggleProjectCollapsed}
                onSelectConversation={onSelectConversation}
                onConversationContextMenu={(e, id) => {
                  e.preventDefault();
                  setConvCtx({ position: { x: e.clientX, y: e.clientY }, convId: id });
                }}
                onRequestConversationContextMenu={(rect, id) => {
                  setConvCtx({ position: { x: rect.right - 180, y: rect.bottom + 4 }, convId: id });
                }}
                onProjectContextMenu={(e, id) => {
                  e.preventDefault();
                  setProjectCtx({ position: { x: e.clientX, y: e.clientY }, projectId: id });
                }}
                onRequestProjectContextMenu={(rect, id) => {
                  setProjectCtx({ position: { x: rect.right - 180, y: rect.bottom + 4 }, projectId: id });
                }}
                onRenameProjectRequest={(id) => {
                  const p = projects.find((x) => x.id === id);
                  if (p) startRenameProject(p);
                }}
                onRenameConversationSubmit={(id, label) => onRenameConversation(id, label)}
              />
              <ChatsSection
                conversations={filteredConversations}
                activeConvId={activeConvId}
                searchQuery=""
                onSelectConversation={onSelectConversation}
                onConversationContextMenu={(e, id) => {
                  e.preventDefault();
                  setConvCtx({ position: { x: e.clientX, y: e.clientY }, convId: id });
                }}
                onRequestConversationContextMenu={(rect, id) => {
                  setConvCtx({ position: { x: rect.right - 180, y: rect.bottom + 4 }, convId: id });
                }}
                onRenameConversationSubmit={(id, label) => onRenameConversation(id, label)}
              />
            </>
          )}
        </div>
      )}

      {!collapsed && (
        <AccountFooter
          account={account}
          onSelectMenuItem={(id) => {
            if (id === "settings") onOpenSettings();
          }}
        />
      )}

      <ConversationContextMenu
        position={convCtx.position}
        conv={convForCtx}
        projects={projects}
        onClose={() => setConvCtx({ position: null, convId: null })}
        onTogglePin={(id) => onTogglePinConversation(id)}
        onStartRename={(id) => {
          const c = conversations.find((x) => x.id === id);
          if (c) startRenameConv(c);
        }}
        onAssignProject={(id, projectId) => onAssignConversationToProject(id, projectId)}
        onArchive={() => {
          setConvCtx({ position: null, convId: null });
        }}
        onDuplicate={() => {
          /* TODO: duplicate conversation */
          setConvCtx({ position: null, convId: null });
        }}
        onRequestDelete={(conv) => setPendingDelete({ kind: "conversation", conv })}
      />

      <ProjectContextMenu
        position={projectCtx.position}
        project={projectForCtx}
        convCount={projectForCtx ? convCountForProject(projectForCtx.id) : 0}
        onClose={() => setProjectCtx({ position: null, projectId: null })}
        onRenameProject={(id) => {
          const p = projects.find((x) => x.id === id);
          if (p) startRenameProject(p);
        }}
        onRequestDelete={(project, count) => setPendingDelete({ kind: "project", project, convCount: count })}
      />

      <SearchModal
        open={searchModalOpen}
        conversations={conversations}
        projects={projects}
        onClose={() => setSearchModalOpen(false)}
        onSelectConversation={(id) => onSelectConversation(id)}
        onSelectProject={(id) => onSelectProject?.(id)}
      />

      <ConfirmDialog
        open={pendingDelete?.kind === "conversation"}
        title="Chat löschen?"
        description={
          pendingDelete?.kind === "conversation"
            ? `»${pendingDelete.conv.label}« wird dauerhaft gelöscht.`
            : undefined
        }
        confirmLabel="Löschen"
        danger
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (pendingDelete?.kind === "conversation") onDeleteConversation(pendingDelete.conv.id);
          setPendingDelete(null);
        }}
      />

      <ConfirmDialog
        open={pendingDelete?.kind === "project"}
        title="Projekt löschen?"
        description={
          pendingDelete?.kind === "project"
            ? `»${pendingDelete.project.name}« wird gelöscht. Zugeordnete Chats bleiben erhalten.`
            : undefined
        }
        confirmLabel="Löschen"
        danger
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (pendingDelete?.kind === "project") onDeleteProject(pendingDelete.project.id);
          setPendingDelete(null);
        }}
      />

      {pendingRename && (
        <div className="rename-prompt-overlay" role="dialog" aria-modal="true" aria-label="Umbenennen">
          <div className="rename-prompt">
            <h3 className="rename-prompt-title">
              {pendingRename.kind === "conversation" ? "Chat umbenennen" : "Projekt umbenennen"}
            </h3>
            <input
              type="text"
              className="conv-rename-input"
              value={renameDraft}
              onChange={(e) => setRenameDraft(e.target.value)}
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter") { e.preventDefault(); commitRename(); }
                if (e.key === "Escape") { setPendingRename(null); setRenameDraft(""); }
              }}
            />
            <div className="rename-prompt-actions">
              <button type="button" className="btn btn-ghost" onClick={() => { setPendingRename(null); setRenameDraft(""); }}>
                Abbrechen
              </button>
              <button type="button" className="btn btn-primary" onClick={commitRename}>
                Speichern
              </button>
            </div>
          </div>
        </div>
      )}

      {!collapsed && <div className={`sidebar-resize-handle${isResizing ? " active" : ""}`} style={{ left: sidebarWidth - 5 }} onMouseDown={handleResizeStart} />}
    </aside>
  );
}
