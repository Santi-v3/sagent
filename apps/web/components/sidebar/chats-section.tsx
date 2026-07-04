"use client";

import { ChatRow } from "./chat-row";
import type { SidebarConversation } from "./types";

export type ChatsSectionProps = {
  conversations: SidebarConversation[];
  activeConvId: string | null;
  onSelectConversation: (id: string) => void;
  onConversationContextMenu: (e: React.MouseEvent, convId: string) => void;
  onRequestConversationContextMenu: (rect: DOMRect, convId: string) => void;
  onRenameConversationSubmit: (id: string, label: string) => void;
};

export function ChatsSection({
  conversations, activeConvId,
  onSelectConversation, onConversationContextMenu,
  onRequestConversationContextMenu, onRenameConversationSubmit,
}: ChatsSectionProps) {
  const filtered = conversations
    .filter((c) => !c.projectId)
    .sort((a, b) => b.updatedAt - a.updatedAt);

  return (
    <section className="sidebar-section" aria-label="Chats">
      <div className="sidebar-section-heading">
        <div className="sidebar-section-title">Chats</div>
      </div>
      {filtered.map((c) => (
        <ChatRow
          key={c.id}
          conv={c}
          active={c.id === activeConvId}
          onSelect={() => onSelectConversation(c.id)}
          onContextMenu={(e) => onConversationContextMenu(e, c.id)}
          onRequestContextMenu={(rect) => onRequestConversationContextMenu(rect, c.id)}
          onRenameSubmit={(label) => onRenameConversationSubmit(c.id, label)}
        />
      ))}
      {filtered.length === 0 && (
        <div className="sidebar-empty">Keine Chats</div>
      )}
    </section>
  );
}
