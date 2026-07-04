"use client";

import { CaretLeft, CaretRight, Sidebar as SidebarIcon } from "@phosphor-icons/react";
import type { MouseEvent } from "react";

export type SidebarTopProps = {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onBack: () => void;
  onForward: () => void;
  canGoBack: boolean;
  canGoForward: boolean;
};

export function SidebarTop({ collapsed, onToggleCollapsed, onBack, onForward, canGoBack, canGoForward }: SidebarTopProps) {
  if (collapsed) {
    return (
      <div className="sidebar-top sidebar-top--collapsed">
        <button
          type="button"
          className="sidebar-top-toggle"
          aria-label="Sidebar ausklappen"
          title="Sidebar ausklappen"
          onClick={onToggleCollapsed}
        >
          <SidebarIcon weight="regular" aria-hidden="true" />
        </button>
      </div>
    );
  }

  return (
    <div className="sidebar-top">
      <div className="sidebar-window-dots" aria-hidden="true">
        <span className="sidebar-window-dot sidebar-window-dot--red" />
        <span className="sidebar-window-dot sidebar-window-dot--yellow" />
        <span className="sidebar-window-dot sidebar-window-dot--green" />
      </div>
      <div className="sidebar-top-actions">
        <button
          type="button"
          className="sidebar-top-toggle"
          aria-label="Sidebar einklappen"
          title="Sidebar einklappen"
          onClick={onToggleCollapsed}
        >
          <SidebarIcon weight="regular" aria-hidden="true" />
        </button>
        <IconButton label="Zurück" disabled={!canGoBack} onClick={onBack}>
          <CaretLeft weight="regular" aria-hidden="true" />
        </IconButton>
        <IconButton label="Vorwärts" disabled={!canGoForward} onClick={onForward}>
          <CaretRight weight="regular" aria-hidden="true" />
        </IconButton>
      </div>
    </div>
  );
}

function IconButton({
  label,
  disabled,
  onClick,
  children,
}: {
  label: string;
  disabled?: boolean;
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      className="sidebar-top-icon-btn"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
