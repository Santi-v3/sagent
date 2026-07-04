"use client";

import { NotePencil, MagnifyingGlass, ClockCounterClockwise, PuzzlePiece } from "@phosphor-icons/react";

export type PrimaryNavProps = {
  collapsed: boolean;
  onNewChat: () => void;
  onOpenSearch: () => void;
};

type NavEntry = {
  id: "new-chat" | "search" | "planned" | "plugins";
  label: string;
  icon: typeof NotePencil;
  onClick: () => void;
};

export function PrimaryNav({ collapsed, onNewChat, onOpenSearch }: PrimaryNavProps) {
  const entries: NavEntry[] = [
    { id: "new-chat", label: "Neuer Chat", icon: NotePencil, onClick: onNewChat },
    { id: "search", label: "Suche", icon: MagnifyingGlass, onClick: onOpenSearch },
    { id: "planned", label: "Geplant", icon: ClockCounterClockwise, onClick: () => {} },
    { id: "plugins", label: "Plugins", icon: PuzzlePiece, onClick: () => {} },
  ];

  return (
    <nav className="sidebar-primary-nav" aria-label="Hauptnavigation">
      {entries.map((entry) => {
        const Icon = entry.icon;
        return (
          <button
            key={entry.id}
            type="button"
            className="sidebar-action"
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
