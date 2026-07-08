"use client";

import {
  ArrowUp, ArrowsClockwise, CheckCircle, CircleNotch,
  Code, Folder, GitBranch, GitDiff as GitDiffIcon,
  Lightbulb, Play, ShieldCheck,
  TerminalWindow, Warning, WarningCircle, X, XCircle,
  Plus, Brain, Wrench, BookOpen,
  List, ImageSquare, Camera, SpeakerHigh,
} from "@phosphor-icons/react";
import { FormEvent, KeyboardEvent, useCallback, useEffect, useRef, useState } from "react";

import { CapabilityPolicyPreview } from "@/components/capability-policy-preview";
import { CloudApprovalPreview } from "@/components/cloud-approval-preview";
import { CodeEditPreviewPanel } from "@/components/code-edit-preview-panel";
import { SettingsPage, type UserModelConfig } from "@/components/settings/settings-page";
import { ConversationToolPerms } from "@/components/chat/conversation-tool-perms";
import { ToolPreviewPanel } from "@/components/chat/tool-preview-panel";
import { SyntaxHighlight, detectLanguage } from "@/components/chat/syntax-highlight";
import { DiffViewer } from "@/components/chat/diff-viewer";
import { ArtifactView } from "@/components/chat/artifact-view";
import { UsageDashboard } from "@/components/usage-dashboard";
import { AutonomousModePanel } from "@/components/autonomous-panel";
import { ExtensionsPage } from "@/components/extensions/extensions-page";
import { LeftSidebar } from "@/components/sidebar/left-sidebar";
import { api } from "@/lib/api-client";
import type { SidebarConversation } from "@/lib/api-client";

type ApprovalState = "pending" | "approved" | "rejected" | "needs_changes";
type ApprovalDecision = Exclude<ApprovalState, "pending">;

type PlanStep = { position: number; title: string; description: string };
type ChangeProposal = { summary: string; risk_level: "low" | "medium" | "high"; affected_files: string[]; required_approvals: string[] };
type PlannedTask = { task_id: string; task: string; goal: string; steps: PlanStep[]; risks: string[]; next_actions: string[]; proposal: ChangeProposal; approval_state: ApprovalState; created_at: string; updated_at: string };
type ApprovalResponse = { message: string; task: PlannedTask };
type TestProfile = { profile_id: string; command: string; working_directory: string; timeout_seconds: number };
type TestResult = { result_id: string; profile_id: string; command: string; exit_code: number; stdout: string; stderr: string; passed: boolean; created_at: string; duration_ms: number; timed_out: boolean; output_truncated: boolean };
type GitFileStatus = { path: string; index_status: string; worktree_status: string; original_path: string | null; sensitive: boolean };
type GitStatus = { branch: string | null; detached: boolean; is_main: boolean; clean: boolean; ahead: number; behind: number; head_sha: string | null; files: GitFileStatus[]; warning: string | null };
type GitDiffState = { patch: string; diff_hash: string; file_count: number; truncated: boolean; secrets_redacted: boolean; sensitive_paths_hidden: number };
type GitBranchResponse = { message: string; status: GitStatus };

type TrCommand = { command_id: string; display_name: string; timeout_seconds: number };

type SafetyLevel = "watchful" | "balanced" | "fullaccess";

const API_URL = process.env.NEXT_PUBLIC_AGENT_API_URL ?? "http://127.0.0.1:8765";

const safetyLevels: { id: SafetyLevel; label: string; desc: string }[] = [
  { id: "watchful", label: "Vorsichtig", desc: "Bei jeder Änderung fragen" },
  { id: "balanced", label: "Ausgewogen", desc: "Kritische Änderungen fragen" },
  { id: "fullaccess", label: "Vollzugriff", desc: "Keine Nachfragen, voller Zugriff" },
];

type Project = { id: string; name: string; createdAt: number };

type Conversation = SidebarConversation;



type ThemeMode = "system" | "light" | "dark";

const featureTabs = [
  { id: "policy", icon: ShieldCheck, label: "Policy", desc: "Sicherheitsrichtlinien einsehen" },
  { id: "code", icon: Code, label: "Code Edit", desc: "Dateiänderungen vorschlagen und prüfen" },
  { id: "git", icon: GitBranch, label: "Git", desc: "Git-Status, Diff & Branches" },
  { id: "tests", icon: Play, label: "Tests", desc: "Test-Runner" },
  { id: "model", icon: Brain, label: "Model", desc: "Lokale Modelle & Jobs" },
  { id: "memory", icon: BookOpen, label: "Memory", desc: "Vektor-Gedächtnis (MVP 3)" },
  { id: "usage", icon: Play, label: "Usage", desc: "Modell-Verbrauch & Statistiken" },
  { id: "autonomous", icon: Lightbulb, label: "Auto", desc: "Autonomer Modus & Vorschläge" },
  { id: "cloud", icon: ShieldCheck, label: "Cloud", desc: "Cloud-Provider & Konfiguration" },
];



function renderInlineMarkdown(text: string) {
  return text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).filter(Boolean).map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={`${part}-${index}`}>{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    }
    return <span key={`${part}-${index}`}>{part}</span>;
  });
}

function CodeBlock({ code, lang }: { code: string; lang?: string }) {
  const isDiff = code.startsWith("diff --git") || (code.includes("\n---") && code.includes("\n+++"));
  if (isDiff) return <DiffViewer diff={code} />;
  return (
    <pre className="code-block">
      <div className="code-block-header">
        <span className="code-block-lang">{lang || detectLanguage(code)}</span>
        <button type="button" className="code-block-copy" onClick={() => navigator.clipboard.writeText(code)}>
          Kopieren
        </button>
      </div>
      <SyntaxHighlight code={code} language={lang} />
    </pre>
  );
}

function ChatMessageContent({ content }: { content: string }) {
  const raw = content.replace(/\r\n/g, "\n");
  const blocks: React.ReactNode[] = [];
  let idx = 0;

  while (idx < raw.length) {
    const fencedMatch = raw.slice(idx).match(/^```(\w*)\s*\n([\s\S]*?)```/m);
    if (fencedMatch && fencedMatch.index === 0) {
      const lang = fencedMatch[1] || "";
      const code = fencedMatch[2];
      blocks.push(<CodeBlock key={`cb-${idx}`} code={code} lang={lang} />);
      idx += fencedMatch[0].length;
      continue;
    }

    const newlineIdx = raw.indexOf("\n", idx);
    const line = raw.slice(idx, newlineIdx === -1 ? undefined : newlineIdx).trimEnd();
    idx = newlineIdx === -1 ? raw.length : newlineIdx + 1;

    if (!line.trim()) continue;

    if (line.trim() === "---") {
      blocks.push(<hr key={`hr-${idx}`} />);
      continue;
    }

    if (line.trimStart().startsWith("🔧")) {
      const toolLines = [line];
      while (idx < raw.length) {
        const nextNewline = raw.indexOf("\n", idx);
        const nextLine = raw.slice(idx, nextNewline === -1 ? undefined : nextNewline).trimEnd();
        if (!nextLine.trim() && toolLines.at(-1)?.trim() === "}") break;
        idx = nextNewline === -1 ? raw.length : nextNewline + 1;
        if (nextLine.trim()) toolLines.push(nextLine);
        if (nextLine.trim() === "}") break;
      }
      blocks.push(
        <div className="tool-output-block" key={`tool-${idx}`}>
          <div className="tool-output-title">
            <Wrench weight="regular" aria-hidden="true" />
            {renderInlineMarkdown(toolLines[0].replace(/^\s*🔧\s*/, ""))}
          </div>
          {toolLines.length > 1 ? <pre>{toolLines.slice(1).join("\n")}</pre> : null}
        </div>,
      );
      continue;
    }

    blocks.push(<p key={`p-${idx}`}>{renderInlineMarkdown(line)}</p>);
  }

  return <div className="model-chat-text">{blocks}</div>;
}

export function SagentShell() {
  const [task, setTask] = useState("");
  const [submittedTask, setSubmittedTask] = useState("");
  const [result, setResult] = useState<PlannedTask | null>(null);
  const [, setApprovalMessage] = useState("");
  const [error, setError] = useState("");
  const [retryDecision, setRetryDecision] = useState<ApprovalDecision | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isApprovalLoading, setIsApprovalLoading] = useState(false);
  const [isApiOnline, setIsApiOnline] = useState(false);
  const [mcpRunning, setMcpRunning] = useState(false);
  const [chatResponse, setChatResponse] = useState<string | null>(null);
  const [chatResponseLoading, setChatResponseLoading] = useState(false);
  const [messages, setMessages] = useState<{role: "user" | "assistant"; content: string}[]>([]);
  const [toolCalls, setToolCalls] = useState<{name: string; status: "running" | "done"}[]>([]);
  const [toolPreviews, setToolPreviews] = useState<{name: string; preview: string; high_risk: boolean; iteration: number}[]>([]);
  const [projectContext, setProjectContext] = useState<{root: string | null; files_loaded: number} | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);

  const [projects, setProjects] = useState<Project[]>([]);
  const [accountData, setAccountData] = useState<{ name: string; plan: string; menuItems?: { id: string; label: string; danger?: boolean }[] }>({
    name: "User",
    plan: "Pilot",
    menuItems: [
      { id: "tools", label: "Werkzeuge" },
      { id: "settings", label: "Einstellungen" },
      { id: "logout", label: "Abmelden", danger: true },
    ],
  });

  const [currentView, setCurrentView] = useState<"chat" | "settings" | "extensions">("chat");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>("system");
  const [splitViewEnabled, setSplitViewEnabled] = useState(false);
  const [selectedArtifactIndex, setSelectedArtifactIndex] = useState(0);

  const [testProfiles, setTestProfiles] = useState<TestProfile[]>([]);
  const [selectedTestProfileId, setSelectedTestProfileId] = useState("");
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [testProfileError, setTestProfileError] = useState("");
  const [isTestProfilesLoading, setIsTestProfilesLoading] = useState(false);
  const [isTestLoading, setIsTestLoading] = useState(false);
  const [retryTest, setRetryTest] = useState(false);
  const [routingInfo, setRoutingInfo] = useState<{target: string; reason: string} | null>(null);
  const [convToolPerms, setConvToolPerms] = useState<Record<string, string>>({});
  const [gitStatus, setGitStatus] = useState<GitStatus | null>(null);
  const [gitDiff, setGitDiff] = useState<GitDiffState | null>(null);
  const [gitError, setGitError] = useState("");
  const [branchName, setBranchName] = useState("");
  const [branchMessage, setBranchMessage] = useState("");
  const [isGitLoading, setIsGitLoading] = useState(true);
  const [isBranchLoading, setIsBranchLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [, setTrCommands] = useState<TrCommand[]>([]);

  const [safetyLevel, setSafetyLevel] = useState<SafetyLevel>("balanced");
  const [showSafetyMenu, setShowSafetyMenu] = useState(false);
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [showFeaturePanel, setShowFeaturePanel] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const [toolPanelOpen, setToolPanelOpen] = useState(false);
  const [artifacts, setArtifacts] = useState<{path: string; content: string; sizeBytes: number}[]>([]);
  const [toolTabs, setToolTabs] = useState<{id: string; label: string; icon: string}[]>([]);
  const [activeToolTab, setActiveToolTab] = useState<string | null>(null);

  const [modelAdapters, setModelAdapters] = useState<{adapter_id: string; provider: string; model: string; capabilities: string[]; transport: string; simulated: boolean; supports_streaming: boolean}[]>([]);
  const [modelStatus, setModelStatus] = useState<Record<string, {available: boolean; rate_limited: boolean; reset_in: number; cooldown: number}>>({});
  const [selectedAdapter, setSelectedAdapter] = useState<string>("");
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const modelDropdownRef = useRef<HTMLDivElement>(null);
  const [showModelSettings, setShowModelSettings] = useState(false);
  const modelSettingsRef = useRef<HTMLDivElement>(null);
  const [convTemperature, setConvTemperature] = useState<number>(0.7);
  const [convMaxTokens, setConvMaxTokens] = useState<number>(2048);
  const [convSystemPrompt, setConvSystemPrompt] = useState<string>("");
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastFallbackSelectedRef = useRef<string | null>(null);
  const [toolTemplates, setToolTemplates] = useState<{id: string; name: string; category: string; description: string; prompt_hint: string}[]>([]);
  const [showTemplatePicker, setShowTemplatePicker] = useState<{name: string} | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [templateParams, setTemplateParams] = useState<Record<string, string>>({});
  const [previewCode, setPreviewCode] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [missingTools, setMissingTools] = useState<{name: string}[]>([]);
  const [cloudConfirmDialog, setCloudConfirmDialog] = useState<{
    provider: string;
    model: string;
    endpoint: string;
    resolve: (confirmed: boolean) => void;
  } | null>(null);

  const localModels = modelAdapters.filter(m => m.transport !== "remote_http");
  const cloudModels = modelAdapters.filter(m => m.transport === "remote_http");
  const [modelPrompt, setModelPrompt] = useState("");
  const [modelJobLoading, setModelJobLoading] = useState(false);
  const [modelJobResult, setModelJobResult] = useState<{job_id: string; state: string; created_at: string; completed_at: string | null; result: {content: string; input_tokens: number; output_tokens: number} | null; error: string | null} | null>(null);
  const modelJobPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isCreatingConvRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);
  const [userModels, setUserModels] = useState<UserModelConfig[]>(() => {
    try {
      const stored = localStorage.getItem("sagent-user-models");
      return stored ? JSON.parse(stored) : [];
    } catch { return []; }
  });

  useEffect(() => {
    localStorage.setItem("sagent-user-models", JSON.stringify(userModels));
  }, [userModels]);

  // Request notification permission on mount
  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
  }, []);

  // Track if window was focused during task

  const allModels = [
    ...modelAdapters,
    ...userModels.map(um => ({
      adapter_id: um.id,
      provider: um.provider,
      model: um.model,
      capabilities: [] as string[],
      transport: "remote_http" as const,
      simulated: false,
      supports_streaming: true,
    })),
  ];
  const selectedAdapterLabel = allModels.find(m => m.adapter_id === selectedAdapter)?.model;
  const selectedModelStatus = modelStatus[selectedAdapter];
  const isSelectedRateLimited = selectedModelStatus && !selectedModelStatus.available;

  function handleAddUserModel(cfg: UserModelConfig) {
    setUserModels(prev => [...prev, cfg]);
  }

  function handleRemoveUserModel(id: string) {
    setUserModels(prev => prev.filter(m => m.id !== id));
  }

  useEffect(() => {
    api.getSidebarData().then((data) => {
      setConversations(data.conversations);
      setProjects(data.projects);
      setAccountData(data.account);
    }).catch(() => {
      // API unreachable — start with empty data
    });
  }, []);

  useEffect(() => { document.documentElement.setAttribute("data-theme", theme); }, [theme]);

  async function saveCurrentConversation(msgs: {role: "user" | "assistant"; content: string}[], firstMsg: string) {
    if (isCreatingConvRef.current) return;
    if (activeConvId) {
      const existing = conversations.find(c => c.id === activeConvId);
      if (existing) {
        const label = existing.label === "Neue Konversation" ? firstMsg.slice(0, 40) : existing.label;
        api.updateConversation(activeConvId, { label, messages: msgs }).catch(() => {});
        setConversations(prev => prev.map(c => c.id === activeConvId ? {...c, label, messages: msgs, updatedAt: Date.now()} : c));
        return;
      }
    }
    isCreatingConvRef.current = true;
    try {
      const conv = await api.createConversation({
        label: firstMsg.slice(0, 40),
        messages: msgs.map(m => ({ role: m.role, content: m.content })),
      });
      setActiveConvId(conv.id);
      setConversations(prev => [conv, ...prev]);
    } catch {
      const localId = Date.now().toString(36);
      const conv: Conversation = { id: localId, label: firstMsg.slice(0, 40), messages: msgs, updatedAt: Date.now(), pinned: false, projectId: null };
      setActiveConvId(localId);
      setConversations(prev => [conv, ...prev]);
    } finally {
      isCreatingConvRef.current = false;
    }
  }

  function startNewConversation() {
    isCreatingConvRef.current = false;
    setSubmittedTask(""); setResult(null); setError(""); setTask("");
    setChatResponse(null); setChatResponseLoading(false); setMessages([]);
    setToolCalls([]); setActiveConvId(null); setArtifacts([]);
    setSidebarOpen(false);
  }

  function switchConversation(id: string) {
    const conv = conversations.find(c => c.id === id);
    if (!conv) return;
    setActiveConvId(id);
    setMessages(conv.messages);
    setChatResponse(null); setChatResponseLoading(false); setSubmittedTask(""); setResult(null); setError("");
    setSidebarOpen(false);
  }

  const [installedTools, setInstalledTools] = useState<{name: string; status: string; description: string}[]>([]);
  const [installedToolsLoading, setInstalledToolsLoading] = useState(false);

  async function fetchInstalledTools() {
    setInstalledToolsLoading(true);
    try {
      const r = await fetch(`${API_URL}/tools/installed`);
      if (r.ok) setInstalledTools(await r.json());
    } catch {}
    finally { setInstalledToolsLoading(false); }
  }

  async function fetchTemplates() {
    try {
      const r = await fetch(`${API_URL}/tools/templates`);
      if (r.ok) setToolTemplates(await r.json());
    } catch {}
  }

  async function installTool(name: string, description: string, templateId?: string) {
    try {
      const body: Record<string, unknown> = { name, description, use_llm: false };
      if (templateId) {
        body.template_id = templateId;
        if (Object.keys(templateParams).length > 0) body.template_params = templateParams;
      }
      const r = await fetch(`${API_URL}/tools/install-auto`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (r.ok) {
        await fetchInstalledTools();
        setSelectedTemplate("");
        setTemplateParams({});
        setShowTemplatePicker(null);
        setToolTabs(prev => {
          if (prev.some(t => t.id === "tools")) return prev;
          return [...prev, { id: "tools", label: "Tools", icon: "🔧" }];
        });
        setActiveToolTab("tools");
      }
    } catch {}
  }

  async function uninstallTool(name: string) {
    try {
      await fetch(`${API_URL}/tools/installed/${encodeURIComponent(name)}`, { method: "DELETE" });
      await fetchInstalledTools();
    } catch {}
  }

  const speak = useCallback((text: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text.replace(/<[^>]*>/g, "").slice(0, 1000));
    utterance.lang = "de-DE";
    utterance.rate = 1.0;
    window.speechSynthesis.speak(utterance);
  }, []);

  const [listening, setListening] = useState(false);
  const recognitionRef = useRef<{ start: () => void; stop: () => void; onresult: ((event: { results: SpeechRecognitionResultList }) => void) | null; onerror: ((event: { error: string }) => void) | null; onend: (() => void) | null } | null>(null);

  const startListening = useCallback(() => {
    const SpeechRecognition = (window as unknown as Record<string, unknown>).SpeechRecognition || (window as unknown as Record<string, unknown>).webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    const recognition = new (SpeechRecognition as new () => { start: () => void; stop: () => void; continuous: boolean; interimResults: boolean; lang: string; onresult: ((event: { results: SpeechRecognitionResultList }) => void) | null; onerror: ((event: { error: string }) => void) | null; onend: (() => void) | null })();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "de-DE";
    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = event.results.length - 1; i >= 0; i--) {
        transcript = event.results[i][0].transcript + transcript;
      }
      setTask(prev => prev + transcript);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }, []);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
  }, []);

  const [memoryInput, setMemoryInput] = useState("");
  const [memoryCategory, setMemoryCategory] = useState("");
  const [memoryQuery, setMemoryQuery] = useState("");
  const [memoryResults, setMemoryResults] = useState<{id: string; text: string; metadata: Record<string, string | number | boolean>; created_at: number; score: number | null; parent_id: string | null}[]>([]);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [memorySearching, setMemorySearching] = useState(false);

  async function storeMemory() {
    const t = memoryInput.trim();
    if (!t) return;
    setMemoryLoading(true);
    try {
      const meta: Record<string, string | number | boolean> = {};
      if (memoryCategory.trim()) meta.category = memoryCategory.trim();
      const r = await fetch(`${API_URL}/memory/store`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: t, metadata: meta }),
      });
      if (r.ok) { setMemoryInput(""); setMemoryCategory(""); await refreshMemory(); }
    } catch {}
    finally { setMemoryLoading(false); }
  }

  async function searchMemory() {
    const q = memoryQuery.trim();
    if (!q) return;
    setMemorySearching(true);
    try {
      const body: Record<string, unknown> = { query: q, n_groups: 10 };
      if (memoryCategory.trim()) body.category = memoryCategory.trim();
      const r = await fetch(`${API_URL}/memory/search/grouped`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (r.ok) setMemoryResults(await r.json());
    } catch {}
    finally { setMemorySearching(false); }
  }

  async function refreshMemory() {
    try {
      const r = await fetch(`${API_URL}/memory`);
      if (r.ok) {
        const entries: typeof memoryResults = await r.json();
        setMemoryResults(entries.reverse());
      }
    } catch {}
  }

  async function deleteMemory(id: string) {
    try {
      const r = await fetch(`${API_URL}/memory/${id}`, { method: "DELETE" });
      if (r.ok) await refreshMemory();
    } catch {}
  }

  function openToolTab(id: string, label: string, icon: string) {
    setToolPanelOpen(true);
    setToolTabs(prev => {
      if (prev.some(t => t.id === id)) return prev;
      return [...prev, { id, label, icon }];
    });
    setActiveToolTab(id);
  }

  function closeToolTab(id: string) {
    const newTabs = toolTabs.filter(t => t.id !== id);
    setToolTabs(newTabs);
    if (activeToolTab === id) {
      setActiveToolTab(newTabs.length > 0 ? newTabs[newTabs.length - 1].id : null);
    }
    if (newTabs.length === 0) setToolPanelOpen(false);
  }

  function toggleToolPanel() {
    setToolPanelOpen(prev => !prev);
  }

  useEffect(() => {
    const c = new AbortController();
    fetch(`${API_URL}/health`, { signal: c.signal }).then(r => setIsApiOnline(r.ok)).catch(() => setIsApiOnline(false));
    return () => c.abort();
  }, []);

  useEffect(() => {
    const c = new AbortController();
    Promise.all([
      fetch(`${API_URL}/git/status`, { signal: c.signal }),
      fetch(`${API_URL}/git/diff`, { signal: c.signal }),
    ]).then(async ([sr, dr]) => {
      if (!sr.ok || !dr.ok) throw new Error();
      const [sd, dd] = await Promise.all([sr.json(), dr.json()]) as [GitStatus, GitDiffState];
      setGitStatus(sd); setGitDiff(dd); setGitError("");
    }).catch((e: unknown) => {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setGitError("Git-Status konnte nicht geladen werden.");
    }).finally(() => setIsGitLoading(false));
    return () => c.abort();
  }, []);

  useEffect(() => {
    fetch(`${API_URL}/agent/test-runs/commands`)
      .then(r => r.json())
      .then((cmds: TrCommand[]) => { setTrCommands(cmds); })
      .catch((e: unknown) => { console.warn("Fehler beim Laden der Test-Kommandos:", e); });
  }, []);

  useEffect(() => {
    fetch(`${API_URL}/models`)
      .then(r => r.json())
      .then((models: typeof modelAdapters) => {
        setModelAdapters(models);
        if (models.length) {
          setSelectedAdapter(prev => prev || models[0].adapter_id);
        }
      })
      .catch((e: unknown) => { console.warn("Fehler beim Laden der Modelle:", e); });
    fetch(`${API_URL}/models/status`)
      .then(r => r.json())
      .then((data: {providers: Record<string, {available: boolean; rate_limited: boolean; reset_in: number; cooldown: number}>}) => {
        setModelStatus(data.providers);
      })
      .catch(() => {});
  }, []);

  const selectedAdapterRef = useRef(selectedAdapter);
  useEffect(() => { selectedAdapterRef.current = selectedAdapter; }, [selectedAdapter]);

  useEffect(() => {
    const interval = setInterval(() => {
      fetch(`${API_URL}/models/status`)
        .then(r => r.json())
        .then((data) => {
          if (!data?.providers) return;
          setModelStatus(prev => ({...prev, ...data.providers}));
          const curSelected = selectedAdapterRef.current;
          if (!curSelected) return;
          const st = data.providers[curSelected];
          if (!st || st.available) return;
          if (lastFallbackSelectedRef.current === curSelected) return;
          const avail = (id: string) => {
            const s = data.providers[id];
            return !s || s.available;
          };
          let next: string | null = modelAdapters.filter(m => m.transport !== "remote_http").find(m => m.adapter_id !== curSelected && avail(m.adapter_id))?.adapter_id ?? null;
          if (!next) {
            next = userModels.find(um => avail(um.id) && um.id !== curSelected)?.id ?? null;
          }
          if (!next) {
            next = modelAdapters.filter(m => m.transport === "remote_http").find(m => m.adapter_id !== curSelected && avail(m.adapter_id))?.adapter_id ?? null;
          }
          if (next && next !== curSelected) {
            lastFallbackSelectedRef.current = curSelected;
            const nextLabel = modelAdapters.find(m => m.adapter_id === next)?.model ?? userModels.find(um => um.id === next)?.label ?? next;
            setToastMessage(`Modell gewechselt: ${nextLabel} (vorheriges war ausgelastet)`);
            if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
            toastTimerRef.current = setTimeout(() => setToastMessage(null), 5000);
            setTimeout(() => setSelectedAdapter(next), 0);
          }
        })
        .catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, [modelAdapters, userModels]);

  useEffect(() => {
    if (!showModelDropdown) return;
    function onDown(e: MouseEvent) {
      if (modelDropdownRef.current && !modelDropdownRef.current.contains(e.target as Node) &&
          !(e.target as Element)?.closest?.(".model-selector")) {
        setShowModelDropdown(false);
      }
    }
    function onKey(e: Event) {
      if ("key" in e && e.key === "Escape") setShowModelDropdown(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [showModelDropdown]);

  useEffect(() => {
    if (!showModelSettings) return;
    function onDown(e: MouseEvent) {
      if (modelSettingsRef.current && !modelSettingsRef.current.contains(e.target as Node)) {
        setShowModelSettings(false);
      }
    }
    function onKey(e: Event) {
      if ("key" in e && e.key === "Escape") setShowModelSettings(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [showModelSettings]);

  function stopModelJobPoll() {
    if (modelJobPollRef.current) { clearInterval(modelJobPollRef.current); modelJobPollRef.current = null; }
  }

  async function pollModelJob(jobId: string) {
    stopModelJobPoll();
    modelJobPollRef.current = setInterval(async () => {
      try {
        const r = await fetch(`${API_URL}/models/jobs/${jobId}`);
        if (!r.ok) { stopModelJobPoll(); setModelJobLoading(false); return; }
        const j = await r.json();
        setModelJobResult(j);
        if (["succeeded", "failed", "cancelled"].includes(j.state)) {
          stopModelJobPoll();
          setModelJobLoading(false);
        }
      } catch { stopModelJobPoll(); setModelJobLoading(false); }
    }, 1000);
  }

  async function startModelJob() {
    if (!selectedAdapter || !modelPrompt.trim()) return;
    setModelJobLoading(true);
    setModelJobResult(null);
    try {
      const r = await fetch(`${API_URL}/models/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ adapter_id: selectedAdapter, prompt: modelPrompt, capability: "chat", max_output_tokens: 512, confirmed: true }),
      });
      if (!r.ok) { setModelJobResult({ job_id: "", state: "failed", created_at: "", completed_at: null, result: null, error: `Fehler ${r.status}` }); setModelJobLoading(false); return; }
      const j = await r.json();
      setModelJobResult(j);
      if (["succeeded", "failed", "cancelled"].includes(j.state)) { setModelJobLoading(false); return; }
      await pollModelJob(j.job_id);
    } catch { setModelJobResult({ job_id: "", state: "failed", created_at: "", completed_at: null, result: null, error: "Verbindungsfehler" }); setModelJobLoading(false); }
  }

  async function cancelModelJob() {
    const job = modelJobResult;
    if (!job?.job_id) return;
    try {
      const r = await fetch(`${API_URL}/models/jobs/${job.job_id}/cancel`, { method: "POST" });
      if (r.ok) {
        const j = await r.json();
        setModelJobResult(j);
      }
    } catch {}
  }

  useEffect(() => {
    return () => stopModelJobPoll();
  }, []);

  useEffect(() => {
    fetch(`${API_URL}/agent/project-context`, { method: "POST" })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.root) setProjectContext(d); })
      .catch(() => {});
    fetch(`${API_URL}/mcp/status`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setMcpRunning(d.running); })
      .catch(() => {});
  }, []);

  const loadTestProfiles = useCallback(async () => {
    setIsTestProfilesLoading(true); setTestProfileError("");
    try {
      const r = await fetch(`${API_URL}/agent/test-profiles`);
      if (!r.ok) throw new Error();
      const profiles = await r.json() as TestProfile[];
      setTestProfiles(profiles);
      setSelectedTestProfileId(p => profiles.some(x => x.profile_id === p) ? p : (profiles[0]?.profile_id ?? ""));
      setIsApiOnline(true);
    } catch { setTestProfileError("Test-Allowlist konnte nicht geladen werden."); setIsApiOnline(false); }
    finally { setIsTestProfilesLoading(false); }
  }, []);

  const handleMcpToggle = useCallback(async () => {
    if (mcpRunning) {
      await fetch(`${API_URL}/mcp/stop`, { method: "POST" });
      setMcpRunning(false);
    } else {
      const r = await fetch(`${API_URL}/mcp/start`, { method: "POST" });
      if (r.ok) { const d = await r.json(); setMcpRunning(d.running); }
    }
  }, [mcpRunning]);

  async function submitTask(event?: FormEvent) {
    event?.preventDefault();
    let t = task.trim();
    if (!t || isLoading) return;
    setIsLoading(true); setError(""); setRetryDecision(null); setResult(null); setApprovalMessage("");
    setTestProfiles([]); setSelectedTestProfileId(""); setTestResult(null); setTestProfileError(""); setRetryTest(false);
      setChatResponse(null); setChatResponseLoading(true);
      setMissingTools([]);
      setToolCalls([]);
    // Parse @cloud / @lokal prefix
    let forceRoute: string | undefined;
    const cloudMatch = t.match(/^@cloud\s+/);
    const lokalMatch = t.match(/^@lokal\s+/i);
    if (cloudMatch) { forceRoute = "cloud"; t = t.slice(cloudMatch[0].length); }
    else if (lokalMatch) { forceRoute = "lokal"; t = t.slice(lokalMatch[0].length); }
    setSubmittedTask(t); setTask("");

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const userMessage: {role: "user"; content: string} = {role: "user", content: t};
    setMessages(prev => [...prev, userMessage]);
    setRoutingInfo(null);
    setToolCalls([]);

    const selectedUserModel = userModels.find(um => um.id === selectedAdapter);
    const isCloudRequest = !!selectedUserModel;
    const cloudConfig = selectedUserModel ? {
      endpoint: selectedUserModel.endpoint || undefined,
      apiKey: selectedUserModel.apiKey,
      model: selectedUserModel.model,
      provider: selectedUserModel.provider,
    } : undefined;

    // Cloud-Bestätigung einholen
    if (isCloudRequest) {
      const confirmed = await new Promise<boolean>(resolve => {
        setCloudConfirmDialog({
          provider: selectedUserModel.provider,
          model: selectedUserModel.model,
          endpoint: selectedUserModel.endpoint || "Standard-API",
          resolve,
        });
      });
      setCloudConfirmDialog(null);
      if (!confirmed) {
        setChatResponseLoading(false);
        setMessages(prev => prev.filter(m => m !== userMessage));
        return;
      }
    }

    try {
      // Dateien als Base64 konvertieren
      const imageB64 = await Promise.all(
        attachedFiles
          .filter(f => f.type.startsWith("image/"))
          .map(f => new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result as string);
            reader.onerror = reject;
            reader.readAsDataURL(f);
          }))
      );

      // Versuche zuerst den Agent Loop mit Streaming
      try {
        const response = await fetch(`${API_URL}/agent/execute/stream`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          signal: controller.signal,
          body: JSON.stringify({
            task: t,
            messages: messages.map(m => ({role: m.role, content: m.content})),
            safety_level: safetyLevel,
            adapter_id: selectedAdapter || undefined,
            cloud_config: cloudConfig,
            cloud_confirmed: !!selectedUserModel,
            tool_permissions: Object.keys(convToolPerms).length > 0 ? convToolPerms : undefined,
            images: imageB64.length > 0 ? imageB64 : undefined,
            temperature: convTemperature !== 0.7 ? convTemperature : undefined,
            max_tokens: convMaxTokens !== 2048 ? convMaxTokens : undefined,
            system_prompt: convSystemPrompt.trim() || undefined,
            force_route: forceRoute,
          }),
        });
        if (!response.ok || !response.body) { setChatResponseLoading(false); return; }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = "";
        let seenError = "";
        const toolCallLog: {name: string; args: string; result?: string}[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          for (const line of chunk.split("\n")) {
            if (!line.startsWith("data: ")) continue;
            try {
              const event = JSON.parse(line.slice(6));
              if (event.type === "routing" && event.target) {
                setRoutingInfo({target: event.target, reason: event.reason || ""});
              } else if (event.type === "text" && event.content) {
                fullText += event.content;
                setChatResponse(fullText);
              } else if (event.type === "tool_call") {
                setToolCalls(prev => [...prev, {name: event.name, status: "running"}]);
                toolCallLog.push({name: event.name, args: event.args || "{}"});
              } else if (event.type === "tool_preview") {
                setToolPreviews(prev => [...prev, {name: event.name, preview: event.preview, high_risk: event.high_risk, iteration: event.iteration}]);
              } else if (event.type === "tool_result" && event.name) {
                setToolCalls(prev => prev.map(tc =>
                  tc.name === event.name && tc.status === "running"
                    ? {...tc, status: "done"} : tc
                ));
                const entry = toolCallLog.find(tc => tc.name === event.name && !tc.result);
                if (entry) {
                  entry.result = event.result;
                  // Artefakt sammeln bei erfolgreichem write_file
                  if (event.name === "write_file") {
                    try {
                      const res = JSON.parse(event.result);
                      if (res.success !== false) {
                        const args = JSON.parse(entry.args);
                        if (args.content) {
                          setArtifacts(prev => [...prev, {
                            path: args.path || res.path || "",
                            content: args.content,
                            sizeBytes: res.size_bytes || args.content.length,
                          }]);
                        }
                      }
                    } catch {}
                  }
                }
              } else if (event.type === "self_diagnosis" && event.missing_tools) {
                const suggestion = event.suggestion || "";
                setMissingTools(event.missing_tools.map((n: string) => ({name: n})));
                fullText += "\n\n---\n🔍 **Selbst-Diagnose**\n" + suggestion + "\n";
                setChatResponse(fullText);
              } else if (event.type === "sub_agent_begin") {
                const subLabel = event.sub_type === "code" ? "Code" : event.sub_type === "search" ? "Suche" : event.sub_type === "test" ? "Test" : event.sub_type;
                fullText += `\n\n---\n⚡ **Sub-Agent: ${subLabel}** – arbeite an: ${event.task || ""}\n`;
                setChatResponse(fullText);
                setRoutingInfo({target: "sub", reason: `${subLabel}-Agent aktiv`});
              } else if (event.type === "sub_agent_end") {
                const subLabel = event.sub_type === "code" ? "Code" : event.sub_type === "search" ? "Suche" : event.sub_type === "test" ? "Test" : event.sub_type;
                fullText += `\n✅ **${subLabel}-Agent** fertig.\n`;
                setChatResponse(fullText);
              } else if (event.type === "sub_agent_error") {
                const subLabel = event.sub_type === "code" ? "Code" : event.sub_type === "search" ? "Suche" : event.sub_type === "test" ? "Test" : event.sub_type;
                fullText += `\n❌ **${subLabel}-Agent** fehlgeschlagen: ${event.error || ""}\n`;
                setChatResponse(fullText);
              } else if (event.type === "error" && event.message) {
                seenError = event.message;
                setChatResponse(fullText || event.message);
              } else if (event.type === "done") {
                let content = fullText || seenError || "Fertig.";
                if (toolCallLog.length > 0) {
                  content += "\n\n---\n**Ausgeführte Werkzeuge:**\n";
                  for (const tc of toolCallLog) {
                    let argsPreview = tc.args;
                    try { const parsed = JSON.parse(tc.args); argsPreview = JSON.stringify(parsed, null, 2); } catch {}
                    content += `\n🔧 \`${tc.name}\` ${argsPreview}\n`;
                  }
                }
                const assistantMsg = {role: "assistant" as const, content};
                const newMsgs = [...messages, userMessage, assistantMsg];
                setMessages(newMsgs);
                setChatResponse(null);
                setChatResponseLoading(false);
                setToolCalls([]);
                setToolPreviews([]);
                await saveCurrentConversation(newMsgs, t);
                if (fullText.length > 20) {
                  try { await fetch(`${API_URL}/memory/store`, {
                    method: "POST", headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({text: fullText.slice(0, 2000), metadata: {category: "chat-response", type: "agent"}}),
                  }); } catch {}
                }
                // Desktop notification when done
                try {
                  if (document.hidden && "Notification" in window && Notification.permission === "granted") {
                    new Notification("Sagent – Aufgabe abgeschlossen", {
                      body: t.length > 80 ? t.slice(0, 80) + "…" : t,
                      icon: "/favicon.ico",
                    });
                  }
                } catch {}
              }
            } catch {}
          }
        }
      if (fullText && !chatResponse) {
        const assistantMsg = {role: "assistant" as const, content: fullText};
        const newMsgs = [...messages, userMessage, assistantMsg];
        setMessages(newMsgs);
        setChatResponse(null);
        setChatResponseLoading(false);
        setToolCalls([]);
        setToolPreviews([]);
      }
    } catch {
      if (controller.signal.aborted) return;
      // Fallback: direktes Model-Streaming ohne Agent Loop
      try {
        const streamR = await fetch(`${API_URL}/models/complete/stream`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: t, adapter_id: selectedAdapter || undefined, cloud_config: cloudConfig }),
          signal: controller.signal,
        });
        if (!streamR.ok || !streamR.body) { setChatResponseLoading(false); return; }
        const reader = streamR.body.getReader();
        const decoder = new TextDecoder();
        let fullText = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          for (const line of chunk.split("\n")) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.done) {
                    const assistantMsg = {role: "assistant" as const, content: fullText};
                    const newMsgs = [...messages, userMessage, assistantMsg];
                    setMessages(newMsgs);
                    setChatResponse(null);
                    setChatResponseLoading(false);
                    await saveCurrentConversation(newMsgs, t);
                    break;
                  }
                if (data.content) {
                  fullText += data.content;
                  setChatResponse(fullText);
                }
                if (data.error) {
                  setChatResponse(data.error);
                  setChatResponseLoading(false);
                }
              } catch {}
            }
          }
        }
        if (fullText && !chatResponse) {
          const assistantMsg = {role: "assistant" as const, content: fullText};
          const newMsgs = [...messages, userMessage, assistantMsg];
          setMessages(newMsgs);
          setChatResponse(null);
          setChatResponseLoading(false);
        }
        } catch {
          if (controller.signal.aborted) return;
          setChatResponse("Verbindung zur API fehlgeschlagen.");
          setChatResponseLoading(false);
        }
      }
    } finally {
      abortRef.current = null;
      setIsLoading(false);
    }
  }

  async function decide(decision: ApprovalDecision) {
    if (!result || result.approval_state !== "pending" || isApprovalLoading) return;
    setIsApprovalLoading(true); setError(""); setRetryDecision(decision); setRetryTest(false);
    try {
      const r = await fetch(`${API_URL}/agent/approve`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ task_id: result.task_id, decision }) });
      if (!r.ok) throw new Error();
      const d = await r.json() as ApprovalResponse;
      setResult(d.task); setApprovalMessage(d.message); setRetryDecision(null); setIsApiOnline(true);
      if (d.task.approval_state === "approved") void loadTestProfiles();
    } catch { setError("Freigabe konnte nicht gespeichert werden."); setIsApiOnline(false); }
    finally { setIsApprovalLoading(false); }
  }

  async function runTests() {
    const p = testProfiles.find(x => x.profile_id === selectedTestProfileId);
    if (!result || result.approval_state !== "approved" || !p || isTestLoading) return;
    setIsTestLoading(true); setError(""); setRetryDecision(null); setRetryTest(true); setTestResult(null);
    try {
      const r = await fetch(`${API_URL}/agent/run-tests`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ task_id: result.task_id, profile_id: p.profile_id, expected_command: p.command, confirmed: true }) });
      if (!r.ok) throw new Error();
      setTestResult(await r.json() as TestResult); setRetryTest(false); setIsApiOnline(true);
    } catch { setError("Testlauf konnte nicht gestartet werden."); setIsApiOnline(false); }
    finally { setIsTestLoading(false); }
  }

  async function refreshGit() {
    setIsGitLoading(true); setGitError("");
    try {
      const [sr, dr] = await Promise.all([fetch(`${API_URL}/git/status`), fetch(`${API_URL}/git/diff`)]);
      if (!sr.ok || !dr.ok) throw new Error();
      const [sd, dd] = await Promise.all([sr.json(), dr.json()]) as [GitStatus, GitDiffState];
      setGitStatus(sd); setGitDiff(dd); setIsApiOnline(true);
    } catch { setGitError("Git-Status konnte nicht geladen werden."); setIsApiOnline(false); }
    finally { setIsGitLoading(false); }
  }

  async function createFeatureBranch(event: FormEvent) {
    event.preventDefault();
    const n = branchName.trim();
    if (!gitStatus || !n || isBranchLoading) return;
    setIsBranchLoading(true); setGitError(""); setBranchMessage("");
    try {
      const r = await fetch(`${API_URL}/git/branch`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: n, expected_current_branch: gitStatus.branch, confirmed: true }) });
      if (!r.ok) { const d = await r.json().catch(() => null) as { detail?: string } | null; setGitError(d?.detail ?? "Branch wurde abgelehnt."); setIsApiOnline(true); return; }
      const d = await r.json() as GitBranchResponse;
      setGitStatus(d.status); setBranchMessage(`Branch „${d.status.branch}“ erstellt.`); setBranchName(""); setIsApiOnline(true); await refreshGit();
    } catch { setGitError("Branch konnte nicht erstellt werden."); setIsApiOnline(false); }
    finally { setIsBranchLoading(false); }
  }

  function retryLastAction() { if (retryTest) { void runTests(); return; } if (retryDecision) { void decide(retryDecision); return; } void submitTask(); }
  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void submitTask(); } }

  function handleFilesSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files || []);
    if (files.length) {
      setAttachedFiles(prev => [...prev, ...files]);
      setShowAttachMenu(false);
    }
    e.target.value = "";
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length) {
      setAttachedFiles(prev => [...prev, ...files]);
    }
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    setIsDragging(false);
  }

  function removeFile(index: number) {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  }

  function handleExampleClick(label: string) {
    setTask(label);
    textareaRef.current?.focus();
  }

  return (
    <>
    <main className="app-shell">
      {currentView === "settings" ? (
        <SettingsPage
          onBack={() => setCurrentView("chat")}
          theme={theme}
          onSetTheme={setTheme}
          userModels={userModels}
          onAddUserModel={handleAddUserModel}
          onRemoveUserModel={handleRemoveUserModel}
        />
      ) : currentView === "extensions" ? (
        <ExtensionsPage
          onBack={() => setCurrentView("chat")}
        />
      ) : (
        <>
      {/* ── Sidebar ── */}
      {sidebarOpen ? (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Navigation schließen"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}
      <LeftSidebar
        className={sidebarOpen ? "mobile-open" : ""}
        conversations={conversations}
        projects={projects}
        activeConvId={activeConvId}
        onSelectConversation={switchConversation}
        onNewChat={startNewConversation}
        onDeleteConversation={(id) => {
          setConversations((prev) => prev.filter((c) => c.id !== id));
          if (activeConvId === id) startNewConversation();
          api.deleteConversation(id).catch(() => {});
        }}
        onRenameConversation={(id, label) => {
          setConversations((prev) => prev.map((c) => (c.id === id ? { ...c, label } : c)));
          api.updateConversation(id, { label }).catch(() => {});
        }}
        onTogglePinConversation={(id) => {
          setConversations((prev) => prev.map((c) => (c.id === id ? { ...c, pinned: !c.pinned } : c)));
          const conv = conversations.find(c => c.id === id);
          if (conv) api.updateConversation(id, { pinned: !conv.pinned }).catch(() => {});
        }}
        onAssignConversationToProject={(convId, projectId) => {
          setConversations((prev) => prev.map((c) => (c.id === convId ? { ...c, projectId } : c)));
          api.updateConversation(convId, { projectId }).catch(() => {});
        }}
        onCreateProject={async (name) => {
          try {
            const p = await api.createProject(name);
            setProjects((prev) => [...prev, p]);
          } catch {
            const localId = Date.now().toString(36);
            setProjects((prev) => [...prev, { id: localId, name, createdAt: Date.now() }]);
          }
        }}
        onDeleteProject={(id) => {
          setProjects((prev) => prev.filter((p) => p.id !== id));
          setConversations((prev) => prev.map((c) => (c.projectId === id ? { ...c, projectId: null } : c)));
          api.deleteProject(id).catch(() => {});
        }}
        onRenameProject={(id, name) => {
          setProjects((prev) => prev.map((p) => (p.id === id ? { ...p, name: name.trim() || p.name } : p)));
          api.updateProject(id, { name: name.trim() }).catch(() => {});
        }}
        onOpenSettings={() => setCurrentView("settings")}
        onOpenExtensions={() => setCurrentView("extensions")}
        onOpenTools={toggleToolPanel}
        onOpenSearch={() => {}}
        account={accountData}
      />

      {/* ── Main Wrap (Area + Tool Panel) ── */}
      <div className="main-wrap">
        <div className="main-area">
          {/* ── Top Bar ── */}
          <header className="topbar">
          <div className="topbar-center">
            <button
              type="button"
              className="mobile-nav-toggle"
              aria-label="Navigation öffnen"
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen(true)}
            >
              <List weight="regular" aria-hidden="true" />
            </button>
            <span className="topbar-brand">Sagent</span>
            {projectContext && (
              <span className="project-context-badge" title={`Projekt: ${projectContext.root}`}>
                <Folder weight="regular" />
                {projectContext.root?.split("/").pop() || "Projekt"}
              </span>
            )}
            <div className="model-selector-wrap">
              <button
                type="button"
                className="model-selector"
                title="Modell auswählen"
                aria-expanded={showModelDropdown}
                onClick={() => setShowModelDropdown(s => !s)}
              >
                <Brain weight="regular" />
                <span>{selectedAdapterLabel || "Modell wählen"}</span>
                {isSelectedRateLimited && <span className="badge badge-warning" style={{fontSize:10}}>Limit</span>}
                <svg width="10" height="6" viewBox="0 0 10 6" fill="none" style={{marginLeft:2}}>
                  <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
              </button>
              {showModelDropdown && (
                <div className="model-dropdown" ref={modelDropdownRef}>
                  {localModels.length > 0 && (
                    <>
                      <div className="model-dropdown-section">Lokale Modelle</div>
                      {localModels.map(m => {
                    const st = modelStatus[m.adapter_id];
                    const unavailable = st && !st.available;
                    return (
                    <button key={m.adapter_id} type="button"
                      className={`model-dropdown-item${selectedAdapter === m.adapter_id ? " active" : ""}${unavailable ? " disabled" : ""}`}
                      disabled={unavailable}
                      onClick={() => { if (!unavailable) { setSelectedAdapter(m.adapter_id); setShowModelDropdown(false); } }}
                      title={unavailable ? `Nicht verfügbar (Cooldown ${Math.ceil(st?.reset_in || st?.cooldown || 0)}s)` : ""}>
                      <span className="model-dropdown-name">
                        {m.model}
                        {unavailable && <span className="model-dropdown-status">{Math.ceil(st?.reset_in || st?.cooldown || 0)}s</span>}
                      </span>
                      <span className="model-dropdown-provider">{m.provider}</span>
                      {m.simulated && <span className="badge badge-warning">Simulation</span>}
                      {!m.simulated && <span className="badge badge-success">Live</span>}
                    </button>
                    );
                  })}
                    </>
                  )}
                  {cloudModels.length > 0 && (
                    <>
                      <div className="model-dropdown-divider" />
                      <div className="model-dropdown-section">Cloud Modelle</div>
                      {cloudModels.map(m => {
                    const st = modelStatus[m.adapter_id];
                    const unavailable = st && !st.available;
                    return (
                      <button key={m.adapter_id} type="button"
                        className={`model-dropdown-item${selectedAdapter === m.adapter_id ? " active" : ""}${unavailable ? " disabled" : ""}`}
                        disabled={unavailable}
                        onClick={() => { if (!unavailable) { setSelectedAdapter(m.adapter_id); setShowModelDropdown(false); } }}
                        title={unavailable ? `Nicht verfügbar (Cooldown ${Math.ceil(st?.reset_in || st?.cooldown || 0)}s)` : ""}>
                        <span className="model-dropdown-name">
                          {m.model}
                          {unavailable && <span className="model-dropdown-status">{Math.ceil(st?.reset_in || st?.cooldown || 0)}s</span>}
                        </span>
                        <span className="model-dropdown-provider">{m.provider}</span>
                      </button>
                    );
                  })}
                    </>
                  )}
                  {userModels.length > 0 && (
                    <>
                      <div className="model-dropdown-divider" />
                      <div className="model-dropdown-section">Eigene Modelle</div>
                      {userModels.map(um => {
                    const st = modelStatus[um.id];
                    const unavailable = st && !st.available;
                    return (
                      <button key={um.id} type="button"
                        className={`model-dropdown-item${selectedAdapter === um.id ? " active" : ""}${unavailable ? " disabled" : ""}`}
                        disabled={unavailable}
                        onClick={() => { if (!unavailable) { setSelectedAdapter(um.id); setShowModelDropdown(false); } }}
                        title={unavailable ? `Nicht verfügbar (Cooldown ${Math.ceil(st?.reset_in || st?.cooldown || 0)}s)` : ""}>
                        <span className="model-dropdown-name">
                          {um.label}
                          {unavailable && <span className="model-dropdown-status">{Math.ceil(st?.reset_in || st?.cooldown || 0)}s</span>}
                        </span>
                        <span className="model-dropdown-provider">{um.provider}</span>
                      </button>
                    );
                  })}
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
          <div className="topbar-right">
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setSplitViewEnabled(s => !s)}
              title={splitViewEnabled ? "Split View aus" : "Split View an"}
              style={{ opacity: splitViewEnabled ? 1 : 0.5 }}>
              {splitViewEnabled ? "⊞" : "⊟"}
            </button>
            <ConversationToolPerms overrides={convToolPerms} onChange={setConvToolPerms} />
            <button type="button" className="theme-toggle" onClick={() => setTheme(t => t === "dark" ? "light" : "dark")} title={`Theme: ${theme}`}>
              {theme === "dark" ? "☀️" : "🌙"}
            </button>
            <button type="button" className={`mcp-status ${mcpRunning ? "active" : ""}`} onClick={handleMcpToggle} title={mcpRunning ? "MCP-Server läuft" : "MCP-Server starten"}>
              <Wrench weight="regular" />
            </button>
            <div className="model-settings-wrap" ref={modelSettingsRef}>
              <button type="button" className="model-settings-btn" aria-expanded={showModelSettings} onClick={() => setShowModelSettings(s => !s)} title="Modell-Einstellungen">
                <Brain weight="regular" />
              </button>
              {showModelSettings && (
                <div className="model-settings-dropdown">
                  <div className="model-settings-item">
                    <label>Temperature</label>
                    <div className="model-settings-slider-row">
                      <input type="range" min="0" max="2" step="0.1" value={convTemperature}
                        onChange={e => setConvTemperature(parseFloat(e.target.value))} />
                      <span className="model-settings-value">{convTemperature.toFixed(1)}</span>
                    </div>
                  </div>
                  <div className="model-settings-item">
                    <label>Max Tokens</label>
                    <select value={convMaxTokens} onChange={e => setConvMaxTokens(parseInt(e.target.value))}>
                      <option value={512}>512</option>
                      <option value={1024}>1,024</option>
                      <option value={2048}>2,048</option>
                      <option value={4096}>4,096</option>
                      <option value={8192}>8,192</option>
                    </select>
                  </div>
                  <div className="model-settings-item">
                    <label>System-Prompt</label>
                    <textarea value={convSystemPrompt} onChange={e => setConvSystemPrompt(e.target.value)}
                      placeholder="Leer lassen für Standard-Prompt" rows={3} />
                  </div>
                </div>
              )}
            </div>
            <div className={`api-status${isApiOnline ? " online" : ""}`}>
              <span className="api-dot" />
              <span>{isApiOnline ? "Online" : "Offline"}</span>
            </div>
            <div className="safety-wrap">
              <button type="button" className="safety-btn" aria-expanded={showSafetyMenu} onClick={() => setShowSafetyMenu(s => !s)}>
                <ShieldCheck weight="regular" aria-hidden="true" />
                {safetyLevels.find(s => s.id === safetyLevel)?.label}
              </button>
              {showSafetyMenu && (
                <div className="safety-dropdown">
                  {safetyLevels.map(level => (
                    <button key={level.id} type="button"
                      className={`safety-option${level.id === safetyLevel ? " active" : ""}`}
                      onClick={() => { setSafetyLevel(level.id); setShowSafetyMenu(false); }}>
                      <strong>{level.label}</strong>
                      <span>{level.desc}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <div className="feature-tabs-topbar">
              {featureTabs.map(tab => {
                const Icon = tab.icon;
                return (
                  <button key={tab.id} type="button"
                    className={`feature-tab-btn${showFeaturePanel === tab.id ? " active" : ""}`}
                    onClick={() => setShowFeaturePanel(showFeaturePanel === tab.id ? null : tab.id)}
                    title={tab.desc}
                    aria-label={tab.label}>
                    <Icon weight="regular" aria-hidden="true" />
                    <span className="feature-tab-label">{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </header>

        {/* ── Chat Area ── */}
        <div className="chat-area">
          {toastMessage && (
            <div className="toast-notification" role="status">
              <ArrowsClockwise weight="regular" />
              <span>{toastMessage}</span>
              <button type="button" className="toast-close" onClick={() => setToastMessage(null)} aria-label="Schließen">×</button>
            </div>
          )}
          <div className="messages">
            {messages.length === 0 && !submittedTask ? (
              <div className="empty-state">
                <div className="welcome-logo">
                  <Brain weight="fill" />
                </div>
                <h1>Sagent</h1>
                <p className="subtitle">Dein lokaler KI-Assistent mit Werkzeugen, Gedächtnis und Cloud-Routing.</p>
                <p className="welcome-hint">Starte eine Konversation oder probiere eine der Schnellaktionen:</p>
                <div className="quick-actions">
                  {["Was kann Sagent?", "Lies die README", "Zeige Git-Status", "💡 Hilfe"].map(label => (
                    <button key={label} type="button" className="quick-action-btn" onClick={() => handleExampleClick(label)}>
                      <Lightbulb weight="regular" />{label}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, i) => (
                <article key={i} className={`message ${msg.role === "user" ? "user-message" : "agent-message"}`}>
                  <p className="message-label">
                    <span className={`avatar ${msg.role === "user" ? "user" : "agent"}`}>
                      {msg.role === "user" ? "U" : "S"}
                    </span>
                    {msg.role === "user" ? "Du" : "Sagent"}
                    {msg.role === "assistant" && <span className="model-badge">qwen2.5-coder:7b</span>}
                    <button type="button" className="btn btn-ghost btn-sm" style={{marginLeft: "auto", opacity: 0.4, fontSize: 11}}
                      onClick={() => speak(msg.content)} title="Vorlesen">
                      <SpeakerHigh size={14} />
                    </button>
                  </p>
                  <ChatMessageContent content={msg.content} />
                </article>
              ))
            )}

            {chatResponse && (
              <article className="message agent-message">
                <p className="message-label">
                  <span className="avatar agent">S</span>
                  Sagent
                  <span className="model-badge">offline</span>
                </p>
                <ChatMessageContent content={chatResponse} />
                {artifacts.length > 0 && (
                  <div className="artifacts-container">
                    {artifacts.map((art, i) => (
                      <ArtifactView key={`${art.path}-${i}`} path={art.path} content={art.content} sizeBytes={art.sizeBytes} />
                    ))}
                  </div>
                )}
              </article>
            )}

            {chatResponseLoading && !chatResponse && (
              <div className="loading-state" role="status">
                <span className="pulse" />
                <span className="pulse" style={{ animationDelay: "0.2s" }} />
                <span className="pulse" style={{ animationDelay: "0.4s" }} />
                {routingInfo ? (
                  <span>
                    {routingInfo.target === "cloud" ? "🌐" : "💻"} Routing: {routingInfo.target === "cloud" ? "Cloud" : "Lokal"} – {routingInfo.reason}
                  </span>
                ) : (
                  <span>Sagent antwortet …</span>
                )}
                {toolPreviews.length > 0 && (
                  <ToolPreviewPanel
                    previews={toolPreviews}
                    onApprove={(name) => {
                      setToolCalls(prev => prev.map(tc => tc.name === name ? {...tc, status: "done"} : tc));
                    }}
                    onReject={(name) => {
                      setToolPreviews(prev => prev.filter(tp => tp.name !== name));
                      setToolCalls(prev => prev.map(tc => tc.name === name ? {...tc, status: "done"} : tc));
                    }}
                    watchfulMode={safetyLevel === "watchful"}
                  />
                )}
                {toolCalls.length > 0 && (
                  <div className="tool-calls-inline">
                    {toolCalls.map((tc, i) => (
                      <span key={i} className="tool-call-chip">
                        🔧 {tc.name} {tc.status === "done" ? "✓" : "⋯"}
                      </span>
                    ))}
                      </div>
                    )}
                  </div>
                )}

            {/* Spacer so content doesn't hit bottom */}
            <div style={{ height: 16 }} />
          </div>
        </div>

        {/* ── Input Area ── */}
        <div className="input-area" onDrop={handleDrop} onDragOver={handleDragOver} onDragLeave={handleDragLeave}>
          {isDragging && (
            <div className="drop-overlay">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span>Dateien ablegen zum Anhängen</span>
            </div>
          )}
          {attachedFiles.length > 0 && (
            <div className="attachment-chips">
              {attachedFiles.map((f, i) => (
                <span key={i} className="chip">
                  {f.type.startsWith("image/")
                    // eslint-disable-next-line @next/next/no-img-element
                    ? <img src={URL.createObjectURL(f)} alt="" className="chip-thumb" />
                    : <Code weight="regular" aria-hidden="true" />}
                  {f.name}
                  <button type="button" className="chip-remove" onClick={() => removeFile(i)} aria-label="Entfernen">×</button>
                </span>
              ))}
            </div>
          )}

          {showAttachMenu && (
            <div className="attach-menu">
              <button type="button" className="attach-menu-item" onClick={() => fileInputRef.current?.click()}>
                <Folder className="attach-menu-icon" weight="regular" aria-hidden="true" />
                <div><strong>Datei</strong><span>Ordner oder Datei auswählen</span></div>
              </button>
              <button type="button" className="attach-menu-item" onClick={() => imageInputRef.current?.click()}>
                <ImageSquare className="attach-menu-icon" weight="regular" aria-hidden="true" />
                <div><strong>Bilder</strong><span>Fotos aus der Galerie auswählen</span></div>
              </button>
              <button type="button" className="attach-menu-item" onClick={() => cameraInputRef.current?.click()}>
                <Camera className="attach-menu-icon" weight="regular" aria-hidden="true" />
                <div><strong>Kamera</strong><span>Foto aufnehmen (Handy)</span></div>
              </button>
            </div>
          )}

          <input ref={fileInputRef} type="file" multiple style={{ display: "none" }} onChange={handleFilesSelected} />
          <input ref={imageInputRef} type="file" accept="image/*" multiple style={{ display: "none" }} onChange={handleFilesSelected} />
          <input ref={cameraInputRef} type="file" accept="image/*" capture="environment" style={{ display: "none" }} onChange={handleFilesSelected} />

          <form className="composer" onSubmit={submitTask}>
            {task.match(/^@(cloud|lokal)\s/i)?.[0] && (
              <span className="badge" style={{
                position: "absolute", top: -20, left: 8, zIndex: 10,
                background: task.startsWith("@cloud") ? "var(--accent)" : "var(--success)",
                color: "#fff", fontSize: "0.75em",
              }}>
                {task.startsWith("@cloud") ? "🌐 Cloud erzwungen" : "💻 Lokal erzwungen"}
              </span>
            )}
            <textarea ref={textareaRef} value={task} onChange={e => setTask(e.target.value)} onKeyDown={handleKeyDown}
              placeholder="Aufgabe an Sagent senden (@cloud / @lokal für erzwungenes Routing)" rows={1} maxLength={4000} />
            <div className="composer-actions">
              <button type="button" className="attach-btn" onClick={() => setShowAttachMenu(s => !s)}
                title="Datei anhängen">
                <Plus weight="bold" aria-hidden="true" />
              </button>
              <button type="button"
                className={`send-btn ${listening ? "cancel-btn" : ""}`}
                onClick={listening ? stopListening : startListening}
                title={listening ? "Aufnahme beenden" : "Spracheingabe"}
                style={{ background: listening ? "var(--danger)" : undefined }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                  <line x1="12" y1="19" x2="12" y2="22"/>
                </svg>
              </button>
              {chatResponseLoading ? (
                <button type="button" className="send-btn cancel-btn" onClick={() => { abortRef.current?.abort(); setChatResponseLoading(false); }}
                  aria-label="Abbrechen">
                  <X weight="bold" aria-hidden="true" />
                </button>
              ) : (
                <button type="submit" className="send-btn" disabled={!task.trim() || isLoading}
                  aria-label="Senden">
                  <ArrowUp weight="bold" aria-hidden="true" />
                </button>
              )}
            </div>
          </form>

          <div className="composer-hint">Shift + Enter für neue Zeile</div>

          {/* ── Feature Panels ── */}
          {showFeaturePanel && (
            <div className="feature-panel">
              <div className="feature-panel-header">
                <span className="feature-panel-title">
                  {(() => { const Icon = featureTabs.find(f => f.id === showFeaturePanel)!.icon; return <Icon weight="regular" style={{ verticalAlign: "middle", marginRight: 6 }} />; })()}
                  {featureTabs.find(f => f.id === showFeaturePanel)?.label}
                </span>
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowFeaturePanel(null)}>Schließen</button>
              </div>

              <div className="feature-panel-body">
                {showFeaturePanel === "policy" && <CapabilityPolicyPreview apiUrl={API_URL} />}
                {showFeaturePanel === "code" && <CodeEditPreviewPanel apiUrl={API_URL} />}
                {showFeaturePanel === "cloud" && <CloudApprovalPreview apiUrl={API_URL} />}

                {showFeaturePanel === "git" && (
                  <>
                    {gitError && (
                      <div className="inline-error" role="alert" style={{ marginTop: 0 }}>
                        <WarningCircle weight="regular" aria-hidden="true" /><span>{gitError}</span>
                        <button type="button" onClick={() => void refreshGit()}>Erneut laden</button>
                      </div>
                    )}
                    {gitStatus && (
                      <>
                        {gitStatus.warning && <div className="git-warning" role="status"><Warning weight="regular" aria-hidden="true" /><span>{gitStatus.warning}</span></div>}
                        <div className="git-summary" style={{ marginTop: 0 }}>
                          <div><GitBranch weight="regular" aria-hidden="true" /><span><small>Branch</small><strong>{gitStatus.branch ?? "Detached HEAD"}</strong></span></div>
                          <div><GitDiffIcon weight="regular" aria-hidden="true" /><span><small>Status</small><strong>{gitStatus.clean ? "Sauber" : `${gitStatus.files.length} geändert`}</strong></span></div>
                          <div><ShieldCheck weight="regular" aria-hidden="true" /><span><small>Remote</small><strong>Push/Merge blockiert</strong></span></div>
                        </div>
                        {gitStatus.files.length > 0 && (
                          <ul className="git-file-list">
                            {gitStatus.files.slice(0, 50).map((f, i) => (
                              <li key={`${f.path}-${i}`}><code>{f.index_status === " " ? "·" : f.index_status}{f.worktree_status === " " ? "·" : f.worktree_status}</code><span>{f.path}</span></li>
                            ))}
                            {gitStatus.files.length > 50 && <li className="git-file-more">+ {gitStatus.files.length - 50} weitere</li>}
                          </ul>
                        )}
                        <form className="form-group" onSubmit={createFeatureBranch}>
                          <label htmlFor="branch-name-panel" className="form-label">Neuer Feature-Branch</label>
                          <div className="form-row">
                            <input id="branch-name-panel" className="form-input" value={branchName} onChange={e => setBranchName(e.target.value)} placeholder="feature/mein-branch" maxLength={100} autoComplete="off" />
                            <button type="submit" className="btn btn-primary btn-sm" disabled={!branchName.trim() || isBranchLoading}>
                              {isBranchLoading ? <CircleNotch className="spin" weight="bold" aria-hidden="true" /> : <GitBranch weight="regular" aria-hidden="true" />}
                              {isBranchLoading ? "Erstellt" : "Erstellen"}
                            </button>
                          </div>
                          <p className="form-hint">Erlaubt: codex/, feature/, fix/, docs/, test/, chore/</p>
                        </form>
                        {branchMessage && <div className="inline-success"><CheckCircle weight="regular" aria-hidden="true" /><span>{branchMessage}</span></div>}
                        <div className="git-diff-panel">
                          <div className="git-diff-heading">
                            <span>Diff</span>
                            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                              <code>{gitDiff?.diff_hash.slice(0, 10) ?? "–"}</code>
                              <button type="button" className="btn btn-sm btn-ghost" disabled={isGitLoading} onClick={() => void refreshGit()}><ArrowsClockwise weight="regular" aria-hidden="true" />Aktualisieren</button>
                            </div>
                          </div>
                          {(gitDiff?.secrets_redacted || gitDiff?.sensitive_paths_hidden) && <div className="git-diff-warning">Sensible Inhalte verborgen.</div>}
                          {gitDiff?.truncated && <div className="git-diff-warning">Diff wurde gekürzt.</div>}
                          <pre tabIndex={0}>{gitDiff?.patch || "Keine Änderungen."}</pre>
                        </div>
                      </>
                    )}
                    {!gitStatus && isGitLoading && <div className="test-profile-loading" role="status">Git-Status wird geladen …</div>}
                  </>
                )}

                {showFeaturePanel === "tests" && (
                  <>
                    <div className="form-group" style={{ marginTop: 0 }}>
                      <label htmlFor="test-profile-panel" className="form-label">Testprofil</label>
                      <div className="form-row">
                        <select id="test-profile-panel" className="form-select" value={selectedTestProfileId}
                          onChange={e => { setSelectedTestProfileId(e.target.value); setTestResult(null); }}>
                          {testProfiles.length === 0 && <option value="">Keine Profile</option>}
                          {testProfiles.map(p => <option key={p.profile_id} value={p.profile_id}>{p.profile_id}</option>)}
                        </select>
                        <button type="button" className="btn btn-primary" disabled={isTestLoading || !selectedTestProfileId || testProfiles.length === 0}
                          onClick={() => void loadTestProfiles()}>
                          <Play weight="fill" aria-hidden="true" />Laden
                        </button>
                      </div>
                    </div>
                    {isTestProfilesLoading && <div className="test-profile-loading" role="status" style={{ marginTop: 8 }}>Testprofile werden geladen …</div>}
                    {testProfileError && (
                      <div className="test-inline-error" role="alert">
                        <WarningCircle weight="regular" aria-hidden="true" /><span>{testProfileError}</span>
                        <button type="button" onClick={() => void loadTestProfiles()}>Erneut laden</button>
                      </div>
                    )}
                    {testProfiles.length > 0 && (
                      <>
                        <div className="test-command-display" style={{ marginTop: 8 }}>
                          <TerminalWindow weight="regular" aria-hidden="true" />
                          <code>{testProfiles.find(p => p.profile_id === selectedTestProfileId)?.command}</code>
                        </div>
                        <div className="btn-group">
                          <button type="button" className="btn btn-primary" disabled={isTestLoading || !selectedTestProfileId} onClick={() => void runTests()}>
                            {isTestLoading ? <CircleNotch className="spin" weight="bold" aria-hidden="true" /> : <Play weight="fill" aria-hidden="true" />}
                            {isTestLoading ? "Läuft" : "Test ausführen"}
                          </button>
                        </div>
                      </>
                    )}
                    {testResult && (
                      <div className={`test-result-card ${testResult.passed ? "passed" : "failed"}`}>
                        <div className="test-result-summary">
                          {testResult.passed ? <CheckCircle weight="regular" aria-hidden="true" /> : <XCircle weight="regular" aria-hidden="true" />}
                          <div>
                            <strong>{testResult.passed ? "Testlauf bestanden" : "Testlauf fehlgeschlagen"}</strong>
                            <span>Exit {testResult.exit_code} · {testResult.duration_ms}ms{testResult.timed_out ? " · Zeitlimit" : ""}</span>
                          </div>
                        </div>
                        <div className="test-logs">
                          <div className="test-logs-heading">
                            <span>Logs</span>
                            {testResult.output_truncated && <span>gekürzt</span>}
                          </div>
                          {testResult.stdout && <><span className="test-log-label">stdout</span><pre tabIndex={0}>{testResult.stdout}</pre></>}
                          {testResult.stderr && <><span className="test-log-label">stderr</span><pre tabIndex={0}>{testResult.stderr}</pre></>}
                          {!testResult.stdout && !testResult.stderr && <p>Keine Ausgabe.</p>}
                        </div>
                      </div>
                    )}
                  </>
                )}
                {showFeaturePanel === "model" && (
                  <div className="model-panel">
                    <div className="card-header">
                      <h2>
                        <Brain weight="regular" style={{ verticalAlign: "middle", marginRight: 6 }} />
                        Lokale Modelle
                      </h2>
                    </div>

                    {modelAdapters.length === 0 ? (
                      <p className="loading-text">Modelle werden geladen...</p>
                    ) : (
                      <div className="model-adapter-list">
                        {modelAdapters.map(a => (
                          <div key={a.adapter_id} className={`model-adapter${selectedAdapter === a.adapter_id ? " active" : ""}`}
                            onClick={() => setSelectedAdapter(a.adapter_id)}>
                            <div className="model-adapter-row">
                              <strong>{a.model}</strong>
                              <span className={`badge ${a.simulated ? "badge-warning" : "badge-success"}`}>
                                {a.simulated ? "Simulation" : "Live"}
                              </span>
                            </div>
                            <div className="model-adapter-meta">
                              <span>{a.provider}</span>
                              <span>{a.transport}</span>
                              <span>{a.capabilities.join(", ")}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="form-group">
                      <label className="form-label">Prompt</label>
                      <textarea className="form-input model-prompt-input" rows={2}
                        placeholder="Nachricht an das Modell..."
                        value={modelPrompt} onChange={e => setModelPrompt(e.target.value)} />
                    </div>

                    <div className="btn-group">
                      <button type="button" className="btn btn-primary" disabled={!selectedAdapter || !modelPrompt.trim() || modelJobLoading}
                        onClick={() => void startModelJob()}>
                        {modelJobLoading ? <CircleNotch className="spin" weight="bold" /> : <Play weight="fill" />}
                        {modelJobLoading ? "Läuft..." : "Absenden"}
                      </button>
                    </div>

                    {modelJobResult && (
                      <div className="model-result">
                        <div className="model-result-header">
                          <span className={`badge ${modelJobResult.state === "succeeded" ? "badge-success" : modelJobResult.state === "failed" || modelJobResult.state === "cancelled" ? "badge-danger" : "badge-info"}`}>
                            {modelJobResult.state}
                          </span>
                          {modelJobResult.completed_at && (
                            <span className="model-result-time">
                              {((new Date(modelJobResult.completed_at).getTime() - new Date(modelJobResult.created_at).getTime()) / 1000).toFixed(1)}s
                            </span>
                          )}
                          {modelJobResult.result && (
                            <span className="model-result-tokens">
                              {modelJobResult.result.input_tokens} in → {modelJobResult.result.output_tokens} out
                            </span>
                          )}
                        </div>
                        {modelJobResult.state === "running" && (
                          <button type="button" className="btn btn-danger btn-sm" onClick={() => void cancelModelJob()}>
                            Abbrechen
                          </button>
                        )}
                        {modelJobResult.result?.content && (
                          <pre className="model-result-content">{modelJobResult.result.content}</pre>
                        )}
                        {modelJobResult.error && (
                          <div className="inline-error" role="alert"><WarningCircle weight="regular" />{modelJobResult.error}</div>
                        )}
                      </div>
                    )}
                    <FineTuneSection apiUrl={API_URL} />
                  </div>
                )}
                {showFeaturePanel === "memory" && (
                  <div className="memory-panel">
                    <div className="card-header">
                      <h2>
                        <BookOpen weight="regular" style={{ verticalAlign: "middle", marginRight: 6 }} />
                        Memory (Vektor-Gedächtnis)
                      </h2>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Text speichern</label>
                      <textarea className="form-input memory-text-input" rows={2}
                        placeholder="Wissen, Entscheidungen, Notizen …"
                        value={memoryInput} onChange={e => setMemoryInput(e.target.value)} />
                      <div className="form-row" style={{ marginTop: 8 }}>
                        <input className="form-input" placeholder="Kategorie (z.B. decision, note, project)"
                          value={memoryCategory} onChange={e => setMemoryCategory(e.target.value)} />
                        <button type="button" className="btn btn-primary btn-sm" disabled={!memoryInput.trim() || memoryLoading}
                          onClick={() => void storeMemory()}>
                          {memoryLoading ? <CircleNotch className="spin" weight="bold" /> : "Speichern"}
                        </button>
                      </div>
                    </div>

                    <div className="form-group">
                      <div className="form-row">
                        <input className="form-input" placeholder="Suche im Gedächtnis …"
                          value={memoryQuery} onChange={e => setMemoryQuery(e.target.value)}
                          onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void searchMemory(); } }} />
                        <button type="button" className="btn btn-sm" disabled={!memoryQuery.trim() || memorySearching}
                          onClick={() => void searchMemory()}>
                          {memorySearching ? <CircleNotch className="spin" weight="bold" /> : "Suchen"}
                        </button>
                      </div>
                    </div>

                    {memoryResults.length > 0 && (
                      <div className="memory-results">
                        <div className="memory-results-header">
                          <span>{memoryResults.length} Ergebnis{memoryResults.length !== 1 ? "se" : ""}</span>
                          <button type="button" className="btn btn-ghost btn-sm" onClick={() => void refreshMemory()}>
                            <ArrowsClockwise weight="regular" />Alle
                          </button>
                        </div>
                        {memoryResults.map(r => {
                          const chunkInfo = r.metadata?.total_chunks
                            ? ` (${Number(r.metadata.chunk) + 1}/${r.metadata.total_chunks})`
                            : "";
                          return (
                          <div key={r.id} className="memory-entry">
                            <div className="memory-entry-text">{r.text}</div>
                            <div className="memory-entry-meta">
                              {r.score != null && <span className="badge badge-info">{(r.score * 100).toFixed(0)}%</span>}
                              {r.metadata?.category && <span className="badge">{r.metadata.category as string}{chunkInfo}</span>}
                              {r.metadata?.type && <span className="badge">{r.metadata.type as string}</span>}
                              <span className="memory-entry-time">{new Date(r.created_at * 1000).toLocaleString()}</span>
                            </div>
                            <button type="button" className="memory-entry-delete" onClick={() => void deleteMemory(r.id)}
                              title="Löschen">×</button>
                          </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
                {showFeaturePanel === "usage" && (
                  <UsageDashboard apiUrl={API_URL} />
                )}
                {showFeaturePanel === "autonomous" && (
                  <div className="memory-panel">
                    <div className="card-header">
                      <h2>
                        <Lightbulb weight="regular" style={{ verticalAlign: "middle", marginRight: 6 }} />
                        Autonomer Modus
                      </h2>
                    </div>
                    <AutonomousModePanel apiUrl={API_URL} />
                  </div>
                )}
              </div>
            </div>
          )}

          {error && (
            <div className="error-banner" role="alert">
              <WarningCircle weight="regular" aria-hidden="true" />
              <span>{error}</span>
              <button type="button" onClick={retryLastAction}>Erneut versuchen</button>
            </div>
          )}
          {missingTools.length > 0 && !chatResponseLoading && (
            <div className="error-banner" style={{borderColor: "var(--accent)", background: "var(--surface1)"}}>
              <span>🔧 Fehlende Werkzeuge erkannt</span>
              <div style={{display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center"}}>
                {missingTools.map(t => (
                  <button key={t.name} type="button" className="btn btn-sm"
                    onClick={() => { void fetchTemplates(); setShowTemplatePicker({name: t.name}); }}>
                    Installiere "{t.name}"
                  </button>
                ))}
              </div>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setMissingTools([])}>×</button>
            </div>
          )}
          {showTemplatePicker && (
            <div className="modal-overlay" onClick={() => setShowTemplatePicker(null)}>
              <div className="modal" onClick={e => e.stopPropagation()} style={{maxWidth: 560}}>
                <div className="modal-header">
                  <h3>Tool installieren: "{showTemplatePicker.name}"</h3>
                </div>
                <div className="modal-body">
                  <div className="form-group">
                    <label className="form-label">Wähle eine Vorlage</label>
                    <select className="form-select" value={selectedTemplate} onChange={e => { setSelectedTemplate(e.target.value); setTemplateParams({}); }}>
                      <option value="">Einfaches Grundgerüst (ohne Vorlage)</option>
                      {toolTemplates.map(tmpl => (
                        <option key={tmpl.id} value={tmpl.id}>{tmpl.name} – {tmpl.description.slice(0, 60)}</option>
                      ))}
                    </select>
                  </div>
                  {selectedTemplate && (() => {
                    const tmpl = toolTemplates.find(t => t.id === selectedTemplate);
                    if (!tmpl) return null;
                    const paramHint = tmpl.prompt_hint;
                    return (
                      <div className="form-group">
                        <label className="form-label">{paramHint}</label>
                        <input className="form-input" placeholder="z.B. docker, kubectl, npm, ..."
                          value={templateParams.cli_tool || ""} onChange={e => setTemplateParams({...templateParams, cli_tool: e.target.value})} />
                        {selectedTemplate === "api-client" && (
                          <input className="form-input" placeholder="Basis-URL (z.B. https://api.example.com)"
                            value={templateParams.base_url || ""} onChange={e => setTemplateParams({...templateParams, base_url: e.target.value})} style={{marginTop: 8}} />
                        )}
                        {selectedTemplate === "database-query" && (
                          <>
                            <input className="form-input" placeholder="DB-Typ: sqlite / postgres / mysql"
                              value={templateParams.db_type || ""} onChange={e => setTemplateParams({...templateParams, db_type: e.target.value})} />
                            <input className="form-input" placeholder="Connection-String (optional)"
                              value={templateParams.connection || ""} onChange={e => setTemplateParams({...templateParams, connection: e.target.value})} style={{marginTop: 8}} />
                          </>
                        )}
                      </div>
                    );
                  })()}
                </div>
                {previewCode && (
                  <div className="form-group" style={{marginTop: 12}}>
                    <label className="form-label">Code-Vorschau (prüfen vor Installation)</label>
                    <pre style={{
                      maxHeight: 200, overflowY: "auto", fontSize: 11,
                      background: "var(--surface2)", padding: 8, borderRadius: 6,
                      whiteSpace: "pre-wrap", wordBreak: "break-all",
                    }}>{previewCode}</pre>
                  </div>
                )}
                <div className="modal-footer">
                  <button type="button" className="btn btn-ghost" onClick={() => { setShowTemplatePicker(null); setPreviewCode(null); }}>Abbrechen</button>
                  <button type="button" className="btn btn-ghost btn-sm"
                    disabled={previewLoading}
                    onClick={async () => {
                      setPreviewLoading(true);
                      try {
                        const r = await fetch(`${API_URL}/tools/suggest`, {
                          method: "POST",
                          headers: {"Content-Type": "application/json"},
                          body: JSON.stringify({
                            name: showTemplatePicker.name,
                            description: `Benutzerdefiniertes Werkzeug: ${showTemplatePicker.name}`,
                            template_id: selectedTemplate || undefined,
                            template_params: Object.keys(templateParams).length > 0 ? templateParams : undefined,
                          }),
                        });
                        if (r.ok) { const d = await r.json(); setPreviewCode(d.code); }
                      } catch {} finally { setPreviewLoading(false); }
                    }}>
                    {previewLoading ? "Lade..." : "Code anzeigen"}
                  </button>
                  <button type="button" className="btn btn-primary"
                    onClick={() => { void installTool(showTemplatePicker.name, `Benutzerdefiniertes Werkzeug: ${showTemplatePicker.name}`, selectedTemplate || undefined); setPreviewCode(null); }}>
                    Installieren
                  </button>
                </div>
              </div>
            </div>
          )}
          </div>
        </div>

        {/* ── Split View Panel ── */}
        {splitViewEnabled && artifacts.length > 0 && (
          <div className="split-view-panel">
            <div className="split-view-header">
              <span className="split-view-title">Code-Ansicht</span>
              <span className="split-view-file">
                {artifacts[selectedArtifactIndex || 0]?.path.split("/").pop() || ""}
              </span>
            </div>
            <div className="split-view-body">
              <ArtifactView
                path={artifacts[selectedArtifactIndex || 0]?.path || ""}
                content={artifacts[selectedArtifactIndex || 0]?.content || ""}
                sizeBytes={artifacts[selectedArtifactIndex || 0]?.sizeBytes || 0}
              />
            </div>
          </div>
        )}
        {splitViewEnabled && artifacts.length === 0 && (
          <div className="split-view-panel">
            <div className="split-view-empty">
              <p style={{ opacity: 0.4, textAlign: "center", padding: 32 }}>
                Keine Artefakte vorhanden.<br />
                <span style={{ fontSize: 13 }}>Artefakte erscheinen hier, sobald der Agent Code erstellt.</span>
              </p>
            </div>
          </div>
        )}

        {/* ── Tool Panel ── */}
        {toolPanelOpen && (
          <aside className="tool-panel" aria-label="Tools">
          {toolTabs.length > 0 ? (
            <>
            <div className="tool-panel-tabs">
              {toolTabs.map(tab => (
                <button key={tab.id} type="button"
                  className={`tool-panel-tab${activeToolTab === tab.id ? " active" : ""}`}
                  onClick={() => setActiveToolTab(tab.id)}>
                  <span className="tool-tab-icon">{tab.icon}</span>
                  <span className="tool-tab-label">{tab.label}</span>
                  <span className="tool-tab-close" onClick={e => { e.stopPropagation(); closeToolTab(tab.id); }}>×</span>
                </button>
              ))}
              <button type="button" className="tool-tab-add" title="Neuen Tab öffnen"
                onClick={() => {
                  const nextId = toolTabs.length + 1;
                  openToolTab(`tab-${nextId}`, `Tab ${nextId}`, "📄");
                }}>+</button>
            </div>
            <div className="tool-panel-content">
              {activeToolTab === "terminal" && (
                <div className="tool-terminal">
                  <div className="tool-terminal-header">
                    <span className="tool-terminal-dot" style={{background:"#ff5f57"}} />
                    <span className="tool-terminal-dot" style={{background:"#ffbd2e"}} />
                    <span className="tool-terminal-dot" style={{background:"#28c840"}} />
                    <span className="tool-terminal-title">bash</span>
                  </div>
                  <div className="tool-terminal-body">
                    <div className="term-line"><span className="term-prompt">$</span> ls -la</div>
                    <div className="term-line term-output">total 24</div>
                    <div className="term-line term-output">drwxr-xr-x  10 user  staff   320 Jun 30 14:23 .</div>
                    <div className="term-line term-output">drwxr-xr-x   5 user  staff   160 Jun 30 10:00 ..</div>
                    <div className="term-line term-output">-rw-r--r--   1 user  staff  1024 Jun 30 14:23 README.md</div>
                    <div className="term-line term-output">drwxr-xr-x   3 user  staff    96 Jun 30 14:23 src</div>
                    <div className="term-line term-output">drwxr-xr-x   2 user  staff    64 Jun 30 14:23 tests</div>
                    <div className="term-line"><span className="term-prompt">$</span> <span className="term-cursor">█</span></div>
                  </div>
                </div>
              )}
              {activeToolTab === "browser" && (
                <div className="tool-browser">
                  <div className="tool-browser-bar">
                    <div className="tool-browser-nav">
                      <span className="browser-nav-btn">←</span>
                      <span className="browser-nav-btn">→</span>
                      <span className="browser-nav-btn">↻</span>
                    </div>
                    <div className="tool-browser-url">
                      <span className="browser-url-icon">🔒</span>
                      <span>https://example.com</span>
                    </div>
                  </div>
                  <div className="tool-browser-body">
                    <iframe src="https://example.com" className="tool-browser-iframe"
                      title="Browser" sandbox="allow-scripts allow-same-origin allow-forms" />
                  </div>
                </div>
              )}
              {activeToolTab === "files" && (
                <div className="tool-files">
                  <div className="tool-files-header">
                    <Folder weight="regular" />
                    <span>Workspace{activeConvId ? ` (Chat: ${conversations.find(c => c.id === activeConvId)?.label ?? activeConvId.slice(0, 8)})` : ""}: sagent</span>
                  </div>
                  <div className="tool-files-tree">
                    {[
                      { name: "apps/", type: "dir", children: ["web/", "agent/"] },
                      { name: "packages/", type: "dir", children: ["core/"] },
                      { name: "docs/", type: "dir" },
                      { name: "tests/", type: "dir" },
                      { name: "README.md", type: "file" },
                      { name: "package.json", type: "file" },
                      { name: "pnpm-lock.yaml", type: "file" },
                      { name: "tsconfig.json", type: "file" },
                    ].map(item => (
                      <div key={item.name} className="tool-file-item">
                        <span className="tool-file-icon">{item.type === "dir" ? "📁" : "📄"}</span>
                        <span className="tool-file-name">{item.name}</span>
                      </div>
                    ))}
                  </div>
                  <div className="tool-files-footer">
                    <span>Nur Lesezugriff · Keine Shell-Ausführung</span>
                  </div>
                </div>
              )}
              {activeToolTab === "tools" && (
                <div className="tool-files">
                  <div className="tool-files-header">
                    <span>🔧</span>
                    <span>Installierte Werkzeuge</span>
                    <button type="button" className="btn btn-ghost btn-sm" style={{marginLeft: "auto"}}
                      onClick={() => void fetchInstalledTools()}>
                      <ArrowsClockwise weight="regular" />
                    </button>
                  </div>
                  <div className="tool-files-tree">
                    {installedTools.length === 0 ? (
                      <div className="tool-panel-empty">
                        <p>Keine benutzerdefinierten Werkzeuge installiert.</p>
                        <p className="text-muted" style={{fontSize: "0.85em", marginTop: 4}}>
                          Fehlende Werkzeuge werden automatisch erkannt und können aus dem Chat installiert werden.
                        </p>
                      </div>
                    ) : (
                      installedTools.map(t => (
                        <div key={t.name} className="tool-file-item">
                          <span className="tool-file-icon">🔧</span>
                          <span className="tool-file-name" style={{flex: 1}}>
                            {t.name}
                            <span className="text-muted" style={{fontSize: "0.85em", marginLeft: 8}}>
                              {t.description ? `– ${t.description.slice(0, 60)}` : ""}
                            </span>
                          </span>
                          <span className={`badge ${t.status === "loaded" ? "badge-success" : "badge-warning"}`}>
                            {t.status}
                          </span>
                          <button type="button" className="memory-entry-delete" style={{position: "relative"}}
                            onClick={() => void uninstallTool(t.name)} title="Entfernen">×</button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
            <div className="tool-panel-actions">
              <button type="button" className="tool-panel-action-btn" onClick={() => openToolTab("terminal", "Terminal", "💻")}>
                <TerminalWindow weight="regular" />Terminal
              </button>
              <button type="button" className="tool-panel-action-btn" onClick={() => openToolTab("browser", "Browser", "🌐")}>
                <span>🌐</span>Browser
              </button>
              <button type="button" className="tool-panel-action-btn" onClick={() => openToolTab("files", "Dateien", "📁")}>
                <Folder weight="regular" />Dateien
              </button>
              <button type="button" className="tool-panel-action-btn" onClick={() => { void fetchInstalledTools(); openToolTab("tools", "Tools", "🔧"); }}>
                <span>🔧</span>Tools
              </button>
            </div>
            </>
          ) : (
            <div className="tool-panel-empty">
              <div className="tool-panel-empty-buttons">
                <button type="button" className="tool-panel-empty-btn" onClick={() => openToolTab("terminal", "Terminal", "💻")}>
                  <TerminalWindow weight="regular" /><span>Terminal</span>
                </button>
                <button type="button" className="tool-panel-empty-btn" onClick={() => openToolTab("browser", "Browser", "🌐")}>
                  <span>🌐</span><span>Browser</span>
                </button>
                <button type="button" className="tool-panel-empty-btn" onClick={() => openToolTab("files", "Dateien", "📁")}>
                  <Folder weight="regular" /><span>Dateien</span>
                </button>
              </div>
            </div>
          )}
        </aside>
      )}
      </div>
      </>)}
    </main>
      {cloudConfirmDialog && (
        <div className="modal-overlay" onClick={() => cloudConfirmDialog.resolve(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Cloud-Modell bestätigen</h3>
            </div>
            <div className="modal-body">
              <p>Deine Anfrage wird an einen externen Cloud-Dienst gesendet:</p>
              <ul>
                <li><strong>Provider:</strong> {cloudConfirmDialog.provider}</li>
                <li><strong>Modell:</strong> {cloudConfirmDialog.model}</li>
                <li><strong>Endpunkt:</strong> {cloudConfirmDialog.endpoint}</li>
              </ul>
              <p className="text-warning">Deine Daten werden an diesen externen Server übertragen. Bist du sicher?</p>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-ghost" onClick={() => cloudConfirmDialog.resolve(false)}>
                Abbrechen
              </button>
              <button type="button" className="btn btn-primary" onClick={() => cloudConfirmDialog.resolve(true)}>
                Ja, Cloud verwenden
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}


/* ── Fine-Tuning Section ── */

function FineTuneSection({ apiUrl }: { apiUrl: string }) {
  const [baseModel, setBaseModel] = useState("");
  const [dataset, setDataset] = useState("");
  const [outputName, setOutputName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [jobs, setJobs] = useState<Array<{
    job_id: string; base_model: string; output_model: string;
    state: string; progress: number; error: string; log: string[];
  }>>([]);
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  const [requirements, setRequirements] = useState<{qlora_available: Record<string, boolean>; recommended: string} | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchJobs = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/models/finetune`);
      if (res.ok) setJobs(await res.json());
    } catch {}
  }, [apiUrl]);

  useEffect(() => {
    fetchJobs();
    fetch(`${apiUrl}/models/finetune/requirements`).then(r => r.ok && r.json()).then(setRequirements).catch(() => {});
    pollRef.current = setInterval(fetchJobs, 3000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [fetchJobs, apiUrl]);

  const startFineTune = useCallback(async () => {
    if (!baseModel.trim() || !dataset.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${apiUrl}/models/finetune`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          base_model: baseModel.trim(),
          dataset: dataset.trim(),
          output_name: outputName.trim() || undefined,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        setError(err.detail || "Fehler beim Starten des Fine-Tunings");
      } else {
        setBaseModel("");
        setDataset("");
        setOutputName("");
        fetchJobs();
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [apiUrl, baseModel, dataset, outputName, fetchJobs]);

  return (
    <div className="finetune-section" style={{ borderTop: "1px solid var(--border)", marginTop: 16, paddingTop: 16 }}>
      <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
        Fine-Tuning (QLoRA)
      </h3>

      {requirements && (
        <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>
          {requirements.recommended}
        </p>
      )}

      <div className="form-group">
        <label className="form-label">Basis-Modell</label>
        <input className="form-input" placeholder="z.B. llama3.2:3b"
          value={baseModel} onChange={e => setBaseModel(e.target.value)} />
      </div>

      <div className="form-group">
        <label className="form-label">Trainingsdaten (JSONL)</label>
        <textarea className="form-input" rows={4}
          placeholder='[{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}, ...]'
          value={dataset} onChange={e => setDataset(e.target.value)} />
      </div>

      <div className="form-group">
        <label className="form-label">Ausgabe-Name (optional)</label>
        <input className="form-input" placeholder="Leer lassen für automatischen Namen"
          value={outputName} onChange={e => setOutputName(e.target.value)} />
      </div>

      {error && <div className="inline-error" role="alert"><WarningCircle weight="regular" />{error}</div>}

      <button type="button" className="btn btn-primary btn-sm" disabled={!baseModel.trim() || !dataset.trim() || loading}
        onClick={startFineTune}>
        {loading ? <CircleNotch className="spin" weight="bold" /> : <Play weight="fill" />}
        {loading ? "Starte..." : "Fine-Tune starten"}
      </button>

      {jobs.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <h4 style={{ fontSize: 13, fontWeight: 500, marginBottom: 6 }}>Jobs</h4>
          {jobs.map(job => (
            <div key={job.job_id} className="model-adapter" style={{ cursor: "pointer" }}
              onClick={() => setExpandedJob(expandedJob === job.job_id ? null : job.job_id)}>
              <div className="model-adapter-row">
                <strong>{job.base_model} → {job.output_model}</strong>
                <span className={`badge ${
                  job.state === "succeeded" ? "badge-success" :
                  job.state === "failed" || job.state === "cancelled" ? "badge-danger" : "badge-info"
                }`}>{job.state}</span>
              </div>
              {job.state === "running" && job.progress > 0 && (
                <div style={{ height: 4, background: "var(--border)", borderRadius: 2, marginTop: 4 }}>
                  <div style={{ height: "100%", width: `${job.progress * 100}%`, background: "var(--accent)", borderRadius: 2 }} />
                </div>
              )}
              {expandedJob === job.job_id && job.log.length > 0 && (
                <pre style={{ fontSize: 11, marginTop: 6, maxHeight: 200, overflow: "auto" }}>
                  {job.log.join("\n")}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
