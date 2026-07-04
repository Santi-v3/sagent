"use client";

import { Sidebar as SidebarIcon } from "@phosphor-icons/react";

export type SidebarTopProps = {
  collapsed: boolean;
  onToggleCollapsed: () => void;
};

export function SidebarTop({ collapsed, onToggleCollapsed }: SidebarTopProps) {
  return (
    <div className={`sidebar-top${collapsed ? " sidebar-top--collapsed" : ""}`}>
      <button
        type="button"
        className="sidebar-top-toggle"
        aria-label={collapsed ? "Sidebar ausklappen" : "Sidebar einklappen"}
        title={collapsed ? "Sidebar ausklappen" : "Sidebar einklappen"}
        onClick={onToggleCollapsed}
      >
        <SidebarIcon weight="regular" aria-hidden="true" />
      </button>
    </div>
  );
}
