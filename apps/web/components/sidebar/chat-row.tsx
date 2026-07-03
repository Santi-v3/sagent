"use client";

import { DotsThreeVertical, PushPin } from "@phosphor-icons/react";
import { useRef, useState } from "react";
import { formatRelativeTime } from "./utils";
import type { SidebarConversation } from "./types";

export type ChatRowProps = {
  conv: SidebarConversation;
  active: boolean;
  indented?: boolean;
  onSelect: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
  onRequestContextMenu: (rect: DOMRect) => void;
  onRenameSubmit: (label: string) => void;
};

export function ChatRow({ conv, active, indented, onSelect, onContextMenu, onRequestContextMenu, onRenameSubmit }: ChatRowProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(conv.label);
  const inputRef = useRef<HTMLInputElement>(null);

  function commit() {
    const next = draft.trim();
    if (next && next !== conv.label) onRenameSubmit(next);
    setEditing(false);
  }

  return (
    <div
      className={`conversation-item-wrap${indented ? " conversation-item-wrap--indented" : ""}`}
      onContextMenu={onContextMenu}
    >
      {editing ? (
        <form
          className="conv-rename-form"
          onSubmit={(ev) => {
            ev.preventDefault();
            commit();
          }}
        >
          <input
            ref={inputRef}
            type="text"
            className="conv-rename-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            autoFocus
            onBlur={commit}
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                setDraft(conv.label);
                setEditing(false);
              }
            }}
          />
        </form>
      ) : (
        <div className="conversation-item-row">
          <button
            type="button"
            className={`conversation-item${active ? " active" : ""}`}
            onClick={onSelect}
            onDoubleClick={() => {
              setDraft(conv.label);
              setEditing(true);
              requestAnimationFrame(() => inputRef.current?.focus());
            }}
          >
            {conv.pinned ? (
              <PushPin className="conv-pin-icon" weight="fill" aria-label="Angeheftet" />
            ) : null}
            <span className="conv-label">{conv.label}</span>
            <span className="conversation-age">{formatRelativeTime(conv.updatedAt)}</span>
          </button>
          <button
            type="button"
            className="conv-burger"
            aria-label="Weitere Aktionen"
            title="Weitere Aktionen"
            onClick={(e) => {
              e.stopPropagation();
              onRequestContextMenu((e.currentTarget as HTMLButtonElement).getBoundingClientRect());
            }}
          >
            <DotsThreeVertical weight="bold" aria-hidden="true" />
          </button>
        </div>
      )}
    </div>
  );
}
