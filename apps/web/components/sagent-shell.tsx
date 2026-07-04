"use client";

import {
  ArrowUp, ArrowsClockwise, CheckCircle, CircleNotch,
  Folder, GitBranch, GitDiff as GitDiffIcon,
  Lightbulb, Play, ShieldCheck,
  TerminalWindow, Warning, WarningCircle, XCircle,
  Plus, Code, Gear,
  Brain, Wrench, BookOpen,
  List, ImageSquare, Camera,
} from "@phosphor-icons/react";
import { FormEvent, KeyboardEvent, useCallback, useEffect, useRef, useState } from "react";

import { CapabilityPolicyPreview } from "@/components/capability-policy-preview";
import { CloudApprovalPreview } from "@/components/cloud-approval-preview";
import { CodeEditPreviewPanel } from "@/components/code-edit-preview-panel";
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

function ChatMessageContent({ content }: { content: string }) {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const blocks: React.ReactNode[] = [];

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index].trimEnd();
    if (!line.trim()) continue;

    if (line.trim() === "---") {
      blocks.push(<hr key={`rule-${index}`} />);
      continue;
    }

    if (line.trimStart().startsWith("🔧")) {
      const toolLines = [line];
      while (index + 1 < lines.length) {
        const nextLine = lines[index + 1];
        if (!nextLine.trim() && toolLines.at(-1)?.trim() === "}") break;
        index += 1;
        if (nextLine.trim()) toolLines.push(nextLine);
        if (nextLine.trim() === "}") break;
      }
      blocks.push(
        <div className="tool-output-block" key={`tool-${index}`}>
          <div className="tool-output-title">
            <Wrench weight="regular" aria-hidden="true" />
            {renderInlineMarkdown(toolLines[0].replace(/^\s*🔧\s*/, ""))}
          </div>
          {toolLines.length > 1 ? <pre>{toolLines.slice(1).join("\n")}</pre> : null}
        </div>,
      );
      continue;
    }

    blocks.push(<p key={`line-${index}`}>{renderInlineMarkdown(line)}</p>);
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
  const [chatResponse, setChatResponse] = useState<string | null>(null);
  const [chatResponseLoading, setChatResponseLoading] = useState(false);
  const [messages, setMessages] = useState<{role: "user" | "assistant"; content: string}[]>([]);
  const [toolCalls, setToolCalls] = useState<{name: string; status: "running" | "done"}[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);

  const [projects, setProjects] = useState<Project[]>([]);
  const [accountData, setAccountData] = useState<{ name: string; plan: string }>({ name: "User", plan: "Pilot" });

  const [showSettings, setShowSettings] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [theme, setTheme] = useState<ThemeMode>("system");

  const [testProfiles, setTestProfiles] = useState<TestProfile[]>([]);
  const [selectedTestProfileId, setSelectedTestProfileId] = useState("");
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [testProfileError, setTestProfileError] = useState("");
  const [isTestProfilesLoading, setIsTestProfilesLoading] = useState(false);
  const [isTestLoading, setIsTestLoading] = useState(false);
  const [retryTest, setRetryTest] = useState(false);
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
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [showFeaturePanel, setShowFeaturePanel] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const [toolPanelOpen, setToolPanelOpen] = useState(false);
  const [toolTabs, setToolTabs] = useState<{id: string; label: string; icon: string}[]>([]);
  const [activeToolTab, setActiveToolTab] = useState<string | null>(null);

  const [modelAdapters, setModelAdapters] = useState<{adapter_id: string; provider: string; model: string; capabilities: string[]; transport: string; simulated: boolean; supports_streaming: boolean}[]>([]);
  const [selectedAdapter, setSelectedAdapter] = useState<string>("");
  const [modelPrompt, setModelPrompt] = useState("");
  const [modelJobLoading, setModelJobLoading] = useState(false);
  const [modelJobResult, setModelJobResult] = useState<{job_id: string; state: string; created_at: string; completed_at: string | null; result: {content: string; input_tokens: number; output_tokens: number} | null; error: string | null} | null>(null);
  const modelJobPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

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
    if (activeConvId) {
      const existing = conversations.find(c => c.id === activeConvId);
      if (existing) {
        const label = existing.label === "Neue Konversation" ? firstMsg.slice(0, 40) : existing.label;
        api.updateConversation(activeConvId, { label, messages: msgs }).catch(() => {});
        setConversations(prev => prev.map(c => c.id === activeConvId ? {...c, label, messages: msgs, updatedAt: Date.now()} : c));
        return;
      }
    }
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
    }
  }

  function startNewConversation() {
    setSubmittedTask(""); setResult(null); setError(""); setTask("");
    setChatResponse(null); setChatResponseLoading(false); setMessages([]);
    setToolCalls([]); setActiveConvId(null);
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

  const [memoryInput, setMemoryInput] = useState("");
  const [memoryCategory, setMemoryCategory] = useState("");
  const [memoryQuery, setMemoryQuery] = useState("");
  const [memoryResults, setMemoryResults] = useState<{id: string; text: string; metadata: Record<string, string | number | boolean>; created_at: number; score: number | null}[]>([]);
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
      const r = await fetch(`${API_URL}/memory/search`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, n_results: 20 }),
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
  }, []);

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

  async function submitTask(event?: FormEvent) {
    event?.preventDefault();
    const t = task.trim();
    if (!t || isLoading) return;
    setIsLoading(true); setError(""); setRetryDecision(null); setResult(null); setApprovalMessage("");
    setTestProfiles([]); setSelectedTestProfileId(""); setTestResult(null); setTestProfileError(""); setRetryTest(false);
      setChatResponse(null); setChatResponseLoading(true);
      setToolCalls([]);
    setSubmittedTask(t); setTask("");
    setIsLoading(false);

    const userMessage: {role: "user"; content: string} = {role: "user", content: t};
    setMessages(prev => [...prev, userMessage]);

    // Versuche zuerst den Agent Loop mit Streaming
    try {
      const response = await fetch(`${API_URL}/agent/execute/stream`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task: t,
          messages: messages.map(m => ({role: m.role, content: m.content})),
        }),
      });
      if (!response.ok || !response.body) { setChatResponseLoading(false); return; }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";
      const toolCallLog: {name: string; args: string; result?: string}[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === "text" && event.content) {
              fullText += event.content;
              setChatResponse(fullText);
            } else if (event.type === "tool_call") {
              setToolCalls(prev => [...prev, {name: event.name, status: "running"}]);
              toolCallLog.push({name: event.name, args: event.args || "{}"});
            } else if (event.type === "tool_result" && event.name) {
              setToolCalls(prev => prev.map(tc =>
                tc.name === event.name && tc.status === "running"
                  ? {...tc, status: "done"} : tc
              ));
              const entry = toolCallLog.find(tc => tc.name === event.name && !tc.result);
              if (entry) entry.result = event.result;
            } else if (event.type === "error" && event.message) {
              setChatResponse(fullText || event.message);
            } else if (event.type === "done") {
              let content = fullText || "Fertig.";
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
              setChatResponseLoading(false);
              setToolCalls([]);
              saveCurrentConversation(newMsgs, t);
              if (fullText.length > 20) {
                try { await fetch(`${API_URL}/memory/store`, {
                  method: "POST", headers: {"Content-Type": "application/json"},
                  body: JSON.stringify({text: fullText.slice(0, 2000), metadata: {category: "chat-response", type: "agent"}}),
                }); } catch {}
              }
            }
          } catch {}
        }
      }
      if (fullText && !chatResponse) {
        let content = fullText;
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
        setChatResponseLoading(false);
        setToolCalls([]);
        saveCurrentConversation(newMsgs, t);
      }
    } catch {
      // Fallback: direktes Model-Streaming ohne Agent Loop
      try {
        const streamR = await fetch(`${API_URL}/models/complete/stream`, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: t }),
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
                  setChatResponse(fullText);
                  const assistantMsg = {role: "assistant" as const, content: fullText};
                  const newMsgs = [...messages, userMessage, assistantMsg];
                  setMessages(newMsgs);
                  setChatResponseLoading(false);
                  saveCurrentConversation(newMsgs, t);
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
          setChatResponse(fullText);
          const assistantMsg = {role: "assistant" as const, content: fullText};
          const newMsgs = [...messages, userMessage, assistantMsg];
          setMessages(newMsgs);
          setChatResponseLoading(false);
          saveCurrentConversation(newMsgs, t);
        }
      } catch {
        setChatResponse("Verbindung zur API fehlgeschlagen.");
        setChatResponseLoading(false);
      }
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

  function removeFile(index: number) {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index));
  }

  function handleExampleClick(label: string) {
    setTask(label);
    textareaRef.current?.focus();
  }

  return (
    <main className="app-shell">
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
        onOpenSettings={() => setShowSettings(true)}
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
            <button
              type="button"
              className="model-selector"
              title="Lokale Modelle öffnen"
              aria-expanded={showFeaturePanel === "model"}
              onClick={() => {
                setShowSettings(false);
                setShowFeaturePanel(showFeaturePanel === "model" ? null : "model");
              }}
            >
              <Brain weight="regular" />
              <span>Lokales Modell</span>
            </button>
          </div>
          <div className="topbar-right">
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
            <button
              type="button"
              className="safety-btn icon-button"
              title="Einstellungen öffnen"
              aria-label="Einstellungen öffnen"
              aria-expanded={showSettings}
              onClick={() => {
                setShowFeaturePanel(null);
                setShowSettings(true);
              }}
            >
              <Gear weight="regular" aria-hidden="true" />
            </button>
            <button type="button" className={`safety-btn tool-toggle${toolPanelOpen ? " active" : ""}`}
              onClick={toggleToolPanel} title="Werkzeuge anzeigen" aria-label="Werkzeuge anzeigen" aria-expanded={toolPanelOpen}>
              <Code weight="regular" aria-hidden="true" />
            </button>
          </div>
        </header>

        {/* ── Chat Area ── */}
        <div className="chat-area">
          <div className="messages">
            {messages.length === 0 && !submittedTask ? (
              <div className="empty-state">
                <h1>Sagent</h1>
                <p className="subtitle">Lokaler KI-Assistent mit Werkzeugen und Gedächtnis.</p>
                <div className="quick-actions">
                  {["Was kann Sagent?", "Lies die README", "Zeige Git-Status"].map(label => (
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
                  </p>
                  <ChatMessageContent content={msg.content} />
                </article>
              ))
            )}

            {chatResponseLoading && (
              <div className="loading-state" role="status">
                <span className="pulse" />
                <span className="pulse" style={{ animationDelay: "0.2s" }} />
                <span className="pulse" style={{ animationDelay: "0.4s" }} />
                <span>Lokales Modell antwortet …</span>
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
        <div className="input-area">
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
            <textarea ref={textareaRef} value={task} onChange={e => setTask(e.target.value)} onKeyDown={handleKeyDown}
              placeholder="Aufgabe an Sagent senden" rows={1} maxLength={4000} />
            <div className="composer-actions">
              <button type="button" className="attach-btn" onClick={() => setShowAttachMenu(s => !s)}
                title="Datei anhängen">
                <Plus weight="bold" aria-hidden="true" />
              </button>
              <button type="submit" className="send-btn" disabled={!task.trim() || isLoading}
                aria-label="Senden">
                <ArrowUp weight="bold" aria-hidden="true" />
              </button>
            </div>
          </form>

          <div className="composer-hint">Shift + Enter für neue Zeile</div>

          {/* ── Settings Panel ── */}
          {showSettings && (
            <div className="settings-panel">
              <div className="settings-header">
                <h2><Gear weight="regular" style={{ verticalAlign: "middle", marginRight: 8 }} />Einstellungen</h2>
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowSettings(false)}>Schließen</button>
              </div>

              <div className="settings-section">
                <h3>Design</h3>
                <div className="theme-selector">
                  {([["system", "System"], ["light", "Hell"], ["dark", "Dunkel"]] as [ThemeMode, string][]).map(([val, label]) => (
                    <button key={val} type="button"
                      className={`theme-option${theme === val ? " active" : ""}`}
                      onClick={() => setTheme(val)}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="settings-section">
                <h3>Werkzeuge</h3>
                <div className="settings-tools">
                  {featureTabs.map(f => (
                    <button key={f.id} type="button"
                      className={`settings-tool-btn${showFeaturePanel === f.id ? " active" : ""}`}
                      onClick={() => {
                        setShowSettings(false);
                        setShowFeaturePanel(f.id);
                      }}
                      title={f.desc}>
                      <f.icon weight="regular" />
                      <div className="settings-tool-info">
                        <strong>{f.label}</strong>
                        <span>{f.desc}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

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
                        {memoryResults.map(r => (
                          <div key={r.id} className="memory-entry">
                            <div className="memory-entry-text">{r.text}</div>
                            <div className="memory-entry-meta">
                              {r.score != null && <span className="badge badge-info">{(r.score * 100).toFixed(0)}%</span>}
                              {r.metadata?.category && <span className="badge">{r.metadata.category}</span>}
                              <span className="memory-entry-time">{new Date(r.created_at * 1000).toLocaleString()}</span>
                            </div>
                            <button type="button" className="memory-entry-delete" onClick={() => void deleteMemory(r.id)}
                              title="Löschen">×</button>
                          </div>
                        ))}
                      </div>
                    )}
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
          </div>
        </div>

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
    </main>
  );
}
