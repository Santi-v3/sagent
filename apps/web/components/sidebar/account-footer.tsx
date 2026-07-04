"use client";

import { UserCircle, SignOut, DotsThreeVertical } from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import type { SidebarAccount, SidebarAccountMenuItem } from "./types";

export type AccountFooterProps = {
  account: SidebarAccount;
  onSelectMenuItem?: (id: string) => void;
};

export function AccountFooter({ account, onSelectMenuItem }: AccountFooterProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="sidebar-user" ref={ref}>
      <div className="sidebar-user-avatar" aria-hidden="true">
        <UserCircle weight="fill" />
      </div>
      <div className="sidebar-user-info">
        <span className="sidebar-user-name">{account.name}</span>
        <span className="sidebar-user-role">{account.plan}</span>
      </div>
      <button
        type="button"
        className="sidebar-user-settings"
        aria-label="Account-Menü"
        title="Account-Menü"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <DotsThreeVertical weight="bold" aria-hidden="true" />
      </button>
      {open && (
        <div className="ctx-menu sidebar-account-menu" role="menu">
          {(account.menuItems ?? defaultMenuItems).map((item) => (
            <button
              key={item.id}
              type="button"
              className={`ctx-menu-item${item.danger ? " danger" : ""}`}
              role="menuitem"
              onClick={() => { setOpen(false); onSelectMenuItem?.(item.id); }}
            >
              {item.danger ? <SignOut weight="regular" aria-hidden="true" /> : <UserCircle weight="regular" aria-hidden="true" />}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

const defaultMenuItems: SidebarAccountMenuItem[] = [
  { id: "settings", label: "Einstellungen" },
  { id: "logout", label: "Abmelden", danger: true },
];
