export type SidebarConversation = {
  id: string;
  label: string;
  messages: { role: "user" | "assistant"; content: string }[];
  updatedAt: number;
  pinned?: boolean;
  projectId?: string | null;
};

export type SidebarProject = {
  id: string;
  name: string;
  createdAt: number;
};

export type SidebarAccountMenuItem = {
  id: string;
  label: string;
  danger?: boolean;
};

export type SidebarAccount = {
  name: string;
  plan: string;
  menuItems?: SidebarAccountMenuItem[];
};

export type LeftSidebarProps = {
  conversations: SidebarConversation[];
  projects: SidebarProject[];
  activeConvId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onDeleteConversation: (id: string) => void;
  onRenameConversation: (id: string, label: string) => void;
  onTogglePinConversation: (id: string) => void;
  onAssignConversationToProject: (id: string, projectId: string | null) => void;
  onCreateProject: (name: string) => void;
  onDeleteProject: (id: string) => void;
  onRenameProject: (id: string, name: string) => void;
  onOpenSettings: () => void;
  onOpenTools: () => void;
  onOpenSearch: () => void;
  onSelectProject?: (id: string) => void;
  account: SidebarAccount;
  initialCollapsed?: boolean;
};
