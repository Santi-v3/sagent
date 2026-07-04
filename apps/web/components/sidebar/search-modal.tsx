"use client";

import { MagnifyingGlass, X } from "@phosphor-icons/react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { SidebarConversation, SidebarProject } from "./types";
import { formatRelativeTime } from "./utils";

export type SearchModalProps = {
  open: boolean;
  conversations: SidebarConversation[];
  projects: SidebarProject[];
  onClose: () => void;
  onSelectConversation: (id: string) => void;
  onSelectProject?: (id: string) => void;
};

export function SearchModal({ open, conversations, projects, onClose, onSelectConversation, onSelectProject }: SearchModalProps) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional: reset query on open
      setQuery("");
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const matchedProjects = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return projects.filter((p) => p.name.toLowerCase().includes(q)).slice(0, 10);
  }, [query, projects]);

  const matchedConversations = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return conversations
      .filter((c) => c.label.toLowerCase().includes(q))
      .sort((a, b) => b.updatedAt - a.updatedAt)
      .slice(0, 50);
  }, [query, conversations]);

  const hasResults = matchedConversations.length > 0 || matchedProjects.length > 0;

  if (!open) return null;
  return (
    <div className="search-modal-overlay" role="dialog" aria-modal="true" aria-label="Chats durchsuchen">
      <div className="search-modal">
        <div className="search-modal-input-row">
          <MagnifyingGlass weight="regular" className="search-modal-icon" aria-hidden="true" />
          <input
            ref={inputRef}
            type="search"
            className="search-modal-input"
            placeholder="Chats durchsuchen…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && matchedConversations.length > 0) {
                onSelectConversation(matchedConversations[0].id);
                onClose();
              }
            }}
          />
          <button
            type="button"
            className="search-modal-close"
            onClick={onClose}
            aria-label="Suche schließen"
            title="Schließen"
          >
            <X weight="regular" aria-hidden="true" />
          </button>
        </div>
        <div className="search-modal-results">
          {query.trim() === "" ? (
            <div className="search-modal-hint">Tippe, um deine Chats zu filtern.</div>
          ) : !hasResults ? (
            <div className="search-modal-hint">Keine Treffer.</div>
          ) : (
            <ul className="search-modal-list">
              {matchedProjects.length > 0 && (
                <li className="search-modal-group-header">Projekte</li>
              )}
              {matchedProjects.map((p) => (
                <li key={p.id}>
                  <button
                    type="button"
                    className="search-modal-item"
                    onClick={() => { onSelectProject?.(p.id); onClose(); }}
                  >
                    <span className="search-modal-label">{p.name}</span>
                    <span className="search-modal-meta">
                      <span className="search-modal-project">Projekt</span>
                    </span>
                  </button>
                </li>
              ))}
              {matchedConversations.length > 0 && (
                <li className="search-modal-group-header">Chats</li>
              )}
              {matchedConversations.map((c) => {
                const project = c.projectId ? projects.find((p) => p.id === c.projectId) : null;
                return (
                  <li key={c.id}>
                    <button
                      type="button"
                      className="search-modal-item"
                      onClick={() => { onSelectConversation(c.id); onClose(); }}
                    >
                      <span className="search-modal-label">{c.label}</span>
                      <span className="search-modal-meta">
                        {project ? <span className="search-modal-project">{project.name}</span> : null}
                        <span className="search-modal-time">{formatRelativeTime(c.updatedAt)}</span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
