export function formatRelativeTime(input: string | number | Date): string {
  const date = input instanceof Date ? input : new Date(input);
  const diffMs = Date.now() - date.getTime();
  if (Number.isNaN(diffMs)) return "";

  const minutes = Math.max(1, Math.floor(diffMs / 60_000));
  if (minutes < 60) return `${minutes} Min.`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    if (hours === 1) return "1 Std.";
    return `${hours} Std.`;
  }

  const days = Math.floor(hours / 24);
  if (days === 1) return "1 Tag";
  return `${days} Tag(e)`;
}

const STORAGE_COLLAPSED = "sagent-sidebar-collapsed";
const STORAGE_PROJECTS_EXPANDED = "sagent-sidebar-projects-expanded";

function safeGet(key: string): string | null {
  if (typeof window === "undefined") return null;
  try { return window.localStorage.getItem(key); } catch { return null; }
}

function safeSet(key: string, value: string) {
  if (typeof window === "undefined") return;
  try { window.localStorage.setItem(key, value); } catch { /* ignore */ }
}

export function loadCollapsed(fallback: boolean): boolean {
  const raw = safeGet(STORAGE_COLLAPSED);
  if (raw === "1") return true;
  if (raw === "0") return false;
  return fallback;
}

export function persistCollapsed(value: boolean) {
  safeSet(STORAGE_COLLAPSED, value ? "1" : "0");
}

export function loadProjectsExpanded(fallback: boolean): boolean {
  const raw = safeGet(STORAGE_PROJECTS_EXPANDED);
  if (raw === "1") return true;
  if (raw === "0") return false;
  return fallback;
}

export function persistProjectsExpanded(value: boolean) {
  safeSet(STORAGE_PROJECTS_EXPANDED, value ? "1" : "0");
}
