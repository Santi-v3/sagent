"use client";

import { Folder, Pencil, PushPin, Trash, Archive, Copy } from "@phosphor-icons/react";
import { useEffect, useRef } from "react";
import type { SidebarConversation, SidebarProject } from "./types";

export type ConvContextMenuProps = {
  position: { x: number; y: number } | null;
  conv: SidebarConversation | null;
  projects: SidebarProject[];
  onClose: () => void;
  onTogglePin: (id: string) => void;
  onStartRename: (id: string) => void;
  onAssignProject: (convId: string, projectId: string | null) => void;
  onArchive: (id: string) => void;
  onDuplicate?: (conv: SidebarConversation) => void;
  onRequestDelete: (conv: SidebarConversation) => void;
};

export function ConversationContextMenu({
  position, conv, projects, onClose, onTogglePin, onStartRename, onAssignProject, onArchive, onDuplicate, onRequestDelete,
}: ConvContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!position) return;
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [position, onClose]);

  if (!position || !conv) return null;
  const isPinned = !!conv.pinned;

  return (
    <>
      <div className="ctx-menu-overlay" onClick={onClose} aria-hidden="true" />
      <div
        ref={ref}
        className="ctx-menu ctx-menu--enter"
        style={{ left: position.x, top: position.y }}
        role="menu"
      >
        <button
          type="button"
          className="ctx-menu-item"
          role="menuitem"
          onClick={() => { onTogglePin(conv.id); onClose(); }}
        >
          <PushPin weight={isPinned ? "fill" : "regular"} aria-hidden="true" />
          {isPinned ? "Loslösen" : "Anheften"}
        </button>
        <button
          type="button"
          className="ctx-menu-item"
          role="menuitem"
          onClick={() => { onStartRename(conv.id); onClose(); }}
        >
          <Pencil weight="regular" aria-hidden="true" />
          Umbenennen
        </button>
        {conv.projectId ? (
          <button
            type="button"
            className="ctx-menu-item"
            role="menuitem"
            onClick={() => { onAssignProject(conv.id, null); onClose(); }}
          >
            <Folder weight="regular" aria-hidden="true" />
            Aus Projekt entfernen
          </button>
        ) : projects.length > 0 ? (
          <>
            {projects.map((p) => (
              <button
                key={p.id}
                type="button"
                className="ctx-menu-item"
                role="menuitem"
                onClick={() => { onAssignProject(conv.id, p.id); onClose(); }}
              >
                <Folder weight="regular" aria-hidden="true" />
                In Projekt »{p.name}«
              </button>
            ))}
          </>
        ) : null}
        <button
          type="button"
          className="ctx-menu-item"
          role="menuitem"
          onClick={() => { onDuplicate?.(conv); onClose(); }}
        >
          <Copy weight="regular" aria-hidden="true" />
          Duplizieren
        </button>
        <button
          type="button"
          className="ctx-menu-item"
          role="menuitem"
          onClick={() => { onArchive(conv.id); onClose(); }}
        >
          <Archive weight="regular" aria-hidden="true" />
          Archivieren
        </button>
        <div className="ctx-menu-divider" />
        <button
          type="button"
          className="ctx-menu-item danger"
          role="menuitem"
          onClick={() => { onRequestDelete(conv); onClose(); }}
        >
          <Trash weight="regular" aria-hidden="true" />
          Löschen
        </button>
      </div>
    </>
  );
}

export type ProjectContextMenuProps = {
  position: { x: number; y: number } | null;
  project: SidebarProject | null;
  convCount: number;
  onClose: () => void;
  onRenameProject: (id: string) => void;
  onRequestDelete: (project: SidebarProject, convCount: number) => void;
};

export function ProjectContextMenu({
  position, project, onClose, onRenameProject, onRequestDelete,
}: ProjectContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!position) return;
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [position, onClose]);

  if (!position || !project) return null;
  return (
    <>
      <div className="ctx-menu-overlay" onClick={onClose} aria-hidden="true" />
      <div
        ref={ref}
        className="ctx-menu ctx-menu--enter"
        style={{ left: position.x, top: position.y }}
        role="menu"
      >
        <button
          type="button"
          className="ctx-menu-item"
          role="menuitem"
          onClick={() => { onRenameProject(project.id); onClose(); }}
        >
          <Pencil weight="regular" aria-hidden="true" />
          Umbenennen
        </button>
        <button
          type="button"
          className="ctx-menu-item"
          role="menuitem"
          disabled
          onClick={() => { onClose(); }}
          title="Noch nicht verfügbar"
        >
          <Folder weight="regular" aria-hidden="true" />
          Farbe ändern
        </button>
        <button
          type="button"
          className="ctx-menu-item"
          role="menuitem"
          disabled
          onClick={() => { onClose(); }}
          title="Noch nicht verfügbar"
        >
          <Archive weight="regular" aria-hidden="true" />
          Archivieren
        </button>
        <div className="ctx-menu-divider" />
        <button
          type="button"
          className="ctx-menu-item danger"
          role="menuitem"
          onClick={() => { onRequestDelete(project, 0); onClose(); }}
        >
          <Trash weight="regular" aria-hidden="true" />
          Löschen
        </button>
      </div>
    </>
  );
}
