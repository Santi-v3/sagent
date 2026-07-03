"use client";

import { NotePencil, MagnifyingGlass, ClockCounterClockwise, PuzzlePiece } from "@phosphor-icons/react";

export type PrimaryNavProps = {
  collapsed: boolean;
  onNewChat: () => void;
  onOpenSearch: () => void;
  onOpenPlanned: () => void;
  onOpenPlugins: () => void;
  activeView: "chats" | "planned" | "plugins";
};

type NavEntry = {
  id: "new-chat" | "search" | "planned" | "plugins";
  label: string;
  icon: typeof NotePencil;
  onClick: () => void;
  active: boolean;
};

export function PrimaryNav({ collapsed, onNewChat, onOpenSearch, onOpenPlanned, onOpenPlugins, activeView }: PrimaryNavProps) {
  const entries: NavEntry[] = [
    { id: "new-chat", label: "Neuer Chat", icon: NotePencil, onClick: onNewChat, active: false },
    { id: "search", label: "Suche", icon: MagnifyingGlass, onClick: onOpenSearch, active: false },
    { id: "planned", label: "Geplant", icon: ClockCounterClockwise, onClick: onOpenPlanned, active: activeView === "planned" },
    { id: "plugins", label: "Plugins", icon: PuzzlePiece, onClick: onOpenPlugins, active: activeView === "plugins" },
  ];

  return (
    <nav className="sidebar-primary-nav" aria-label="Hauptnavigation">
      {entries.map((entry) => {
        const Icon = entry.icon;
        return (
          <button
            key={entry.id}
            type="button"
            className={`sidebar-action${entry.active ? " active" : ""}${collapsed ? " sidebar-action--collapsed" : ""}`}
            onClick={entry.onClick}
            aria-label={collapsed ? entry.label : undefined}
            title={collapsed ? entry.label : undefined}
            data-testid={`primary-nav-${entry.id}`}
          >
            <Icon weight="regular" aria-hidden="true" />
            {!collapsed && <span>{entry.label}</span>}
          </button>
        );
      })}
    </nav>
  );
}
