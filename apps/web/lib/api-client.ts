const API_URL = process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://127.0.0.1:8765";

export type SidebarMessage = { role: "user" | "assistant"; content: string };

export type SidebarConversation = {
  id: string;
  label: string;
  messages: SidebarMessage[];
  updatedAt: number;
  pinned: boolean;
  projectId: string | null;
};

export type SidebarProject = {
  id: string;
  name: string;
  createdAt: number;
};

export type SidebarAccount = {
  name: string;
  plan: string;
  menuItems: { id: string; label: string; danger?: boolean }[];
};

export type SidebarData = {
  conversations: SidebarConversation[];
  projects: SidebarProject[];
  account: SidebarAccount;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json();
}

export const api = {
  // ── Aggregated ──
  getSidebarData(): Promise<SidebarData> {
    return request<SidebarData>("/sidebar/data");
  },

  // ── Conversations ──
  listConversations(): Promise<SidebarConversation[]> {
    return request<SidebarConversation[]>("/sidebar/conversations");
  },

  getConversation(id: string): Promise<SidebarConversation> {
    return request<SidebarConversation>(`/sidebar/conversations/${id}`);
  },

  createConversation(data: {
    label?: string;
    messages?: SidebarMessage[];
    projectId?: string | null;
  }): Promise<SidebarConversation> {
    return request<SidebarConversation>("/sidebar/conversations", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  updateConversation(
    id: string,
    data: { label?: string; pinned?: boolean; projectId?: string | null; messages?: SidebarMessage[] }
  ): Promise<SidebarConversation> {
    return request<SidebarConversation>(`/sidebar/conversations/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  deleteConversation(id: string): Promise<void> {
    return request<void>(`/sidebar/conversations/${id}`, { method: "DELETE" });
  },

  // ── Projects ──
  listProjects(): Promise<SidebarProject[]> {
    return request<SidebarProject[]>("/sidebar/projects");
  },

  createProject(name: string): Promise<SidebarProject> {
    return request<SidebarProject>("/sidebar/projects", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
  },

  updateProject(id: string, data: { name?: string }): Promise<SidebarProject> {
    return request<SidebarProject>(`/sidebar/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  deleteProject(id: string): Promise<void> {
    return request<void>(`/sidebar/projects/${id}`, { method: "DELETE" });
  },

  // ── Account ──
  getAccount(): Promise<SidebarAccount> {
    return request<SidebarAccount>("/sidebar/account");
  },
};
