/**
 * IDE Store - Atmos Mode
 * Minimal state: open files, active file, editor state, project info
 * No approvals. No intents. No diffs. No reviews.
 */

import { create } from 'zustand';

// ─── Workspace Mode ─────────────────────────────────────────────────────────
export type WorkspaceMode = 'empty' | 'project';

// ─── Project State (simplified) ─────────────────────────────────────────────
export type ProjectState = 'no_project' | 'loaded' | 'ai_running';

export interface ProjectInfo {
  id: string;
  name: string;
  path?: string;
}

// ─── Activity Log (passive, for visibility only) ────────────────────────────
export interface AIActivityEntry {
  id: string;
  timestamp: number;
  action: string;
  detail?: string;
  success?: boolean;
}

// ─── Terminal Output (shared between chat and terminal panel) ────────────────
export type TerminalLineType = "command" | "stdout" | "stderr";
export interface TerminalLine {
  type: TerminalLineType;
  text: string;
}

// ─── Chat Messages (Atoms chat panel) ─────────────────────────────────────
export type ChatFileStatus = 'pending' | 'generating' | 'done';

export interface ChatFileItem {
  path: string;
  status: ChatFileStatus;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  isStreaming?: boolean;
  files?: ChatFileItem[];
}

// ─── File Status ──────────────────────────────────────────────────────────
export interface FileStatus {
  isNew?: boolean;
  isModified?: boolean;
  isAIGenerated?: boolean;
  isLiveWriting?: boolean;
}

// ─── AI Status + Agent Pipeline ───────────────────────────────────────────
export type AIStatus = 'idle' | 'thinking' | 'generating' | 'streaming' | 'done' | 'error';

export interface AgentStep {
  id: string;
  agent: string;
  name: string;
  icon: string;
  description: string;
  status: 'running' | 'done';
  result?: string;
}

// ─── Store ──────────────────────────────────────────────────────────────────

interface IDEState {
  // Editor tabs
  openFiles: string[];
  activeFile: string | null;
  fileContents: Record<string, string>;
  fileStatuses: Record<string, FileStatus>;
  openFile: (path: string) => void;
  closeFile: (path: string) => void;
  setActiveFile: (path: string | null) => void;
  updateFileContent: (path: string, content: string) => void;

  // Workspace mode
  workspaceMode: WorkspaceMode;
  setWorkspaceMode: (mode: WorkspaceMode) => void;
  resetToEmptyWorkspace: () => void;

  // Project
  projectState: ProjectState;
  project: ProjectInfo | null;
  setProject: (p: ProjectInfo | null) => void;
  setProjectState: (s: ProjectState) => void;

  // Activity log (passive visibility only - never controls execution)
  activityLog: AIActivityEntry[];
  addActivity: (action: string, detail?: string, success?: boolean) => void;
  clearActivity: () => void;

  // Workspace awareness (passive signals, no UI)
  recentlyOpenedFiles: string[];
  recentlyModifiedFiles: string[];
  activeContextFiles: string[];
  markOpened: (path: string) => void;
  markModified: (path: string) => void;
  setActiveContext: (paths: string[]) => void;

  // Terminal output (shared)
  terminalLines: TerminalLine[];
  appendTerminalLine: (text: string, type?: TerminalLineType) => void;
  clearTerminal: () => void;

  // Chat messages
  chatMessages: ChatMessage[];
  addChatMessage: (msg: Omit<ChatMessage, 'id'> & { id?: string }) => void;
  updateLastAssistantMessage: (content: string) => void;
  appendToLastAssistantMessage: (token: string) => void;
  clearChat: () => void;

  // AI status + file writing
  aiStatus: AIStatus;
  setAIStatus: (status: AIStatus) => void;
  aiCurrentFile: string | null;
  setAICurrentFile: (path: string | null) => void;
  aiFileProgress: { index: number; total: number } | null;
  setAIFileProgress: (index: number, total: number) => void;
  fileLiveWriting: Record<string, boolean>;
  setFileLiveWriting: (path: string, isLive: boolean) => void;

  // File operations from chat
  createFile: (path: string, content: string, openAfter?: boolean) => void;
  appendToFile: (path: string, delta: string) => void;

  // Agent pipeline steps
  agentSteps: AgentStep[];
  addAgentStep: (step: Omit<AgentStep, 'id' | 'status'>) => void;
  completeAgentStep: (agent: string, result?: string) => void;
  clearAgentSteps: () => void;
}

const makeId = () => Math.random().toString(36).slice(2, 11);

export const useIDEStore = create<IDEState>((set, get) => ({
  // ─── Editor Tabs ──────────────────────────────────────────────────────────
  openFiles: [],
  activeFile: null,
  fileContents: {},
  fileStatuses: {},

  openFile: (path) => {
    const { openFiles, fileContents, markOpened, setActiveContext } = get();
    if (!openFiles.includes(path)) {
      set({
        openFiles: [...openFiles, path],
        fileContents: {
          ...fileContents,
          [path]: fileContents[path] ?? '',
        },
      });
    }
    set({ activeFile: path });
    // Workspace awareness signals
    markOpened(path);
    setActiveContext([path]);
  },

  closeFile: (path) => {
    const { openFiles, activeFile } = get();
    const next = openFiles.filter((f) => f !== path);
    set({
      openFiles: next,
      activeFile:
        path === activeFile
          ? next.length
            ? next[next.length - 1]
            : null
          : activeFile,
    });
  },

  setActiveFile: (path) => set({ activeFile: path }),

  updateFileContent: (path, content) =>
    set((state) => ({
      fileContents: { ...state.fileContents, [path]: content },
      fileStatuses: {
        ...state.fileStatuses,
        [path]: {
          ...state.fileStatuses[path],
          isModified: true,
        },
      },
    })),

  // ─── Workspace ────────────────────────────────────────────────────────────
  workspaceMode: 'empty',
  setWorkspaceMode: (mode) => set({ workspaceMode: mode }),

  resetToEmptyWorkspace: () =>
    set({
      workspaceMode: 'empty',
      project: null,
      projectState: 'no_project',
      openFiles: [],
      activeFile: null,
      fileContents: {},
    }),

  // ─── Project ──────────────────────────────────────────────────────────────
  projectState: 'no_project',
  project: null,

  setProject: (p) =>
    set({
      project: p,
      projectState: p ? 'loaded' : 'no_project',
    }),

  setProjectState: (s) => set({ projectState: s }),

  // ─── Activity Log (passive only) ──────────────────────────────────────────
  activityLog: [],

  addActivity: (action, detail, success) =>
    set((s) => ({
      activityLog: [
        ...s.activityLog,
        {
          id: makeId(),
          timestamp: Date.now(),
          action,
          detail,
          success,
        },
      ].slice(-50), // Keep last 50 entries
    })),

  clearActivity: () => set({ activityLog: [] }),

  // ─── Workspace Awareness (passive, no UI) ──────────────────────────────────
  recentlyOpenedFiles: [],
  recentlyModifiedFiles: [],
  activeContextFiles: [],

  markOpened: (path) =>
    set((s) => ({
      recentlyOpenedFiles: [
        path,
        ...s.recentlyOpenedFiles.filter((p) => p !== path),
      ].slice(0, 10),
    })),

  markModified: (path) =>
    set((s) => ({
      recentlyModifiedFiles: [
        path,
        ...s.recentlyModifiedFiles.filter((p) => p !== path),
      ].slice(0, 10),
    })),

  setActiveContext: (paths) =>
    set({
      activeContextFiles: Array.from(new Set(paths.filter(Boolean))).slice(0, 10),
    }),

  // ─── Terminal Output (shared) ──────────────────────────────────────────────
  terminalLines: [],

  appendTerminalLine: (text, type = "stdout") =>
    set((s) => ({
      terminalLines: [...s.terminalLines, { type, text }].slice(-500),
    })),

  clearTerminal: () => set({ terminalLines: [] }),

  // ─── Chat messages ──────────────────────────────────────────────────────
  chatMessages: [],

  addChatMessage: (msg) =>
    set((s) => ({
      chatMessages: [...s.chatMessages, { id: msg.id ?? makeId(), ...msg }],
    })),

  updateLastAssistantMessage: (content) =>
    set((s) => {
      const next = [...s.chatMessages];
      for (let i = next.length - 1; i >= 0; i--) {
        if (next[i].role === 'assistant') {
          next[i] = { ...next[i], content };
          break;
        }
      }
      return { chatMessages: next };
    }),

  appendToLastAssistantMessage: (token) =>
    set((s) => {
      const next = [...s.chatMessages];
      for (let i = next.length - 1; i >= 0; i--) {
        if (next[i].role === 'assistant') {
          next[i] = { ...next[i], content: next[i].content + token };
          break;
        }
      }
      return { chatMessages: next };
    }),

  clearChat: () => set({ chatMessages: [] }),

  // ─── AI status + file writing ───────────────────────────────────────────
  aiStatus: 'idle',
  setAIStatus: (status) => set({ aiStatus: status }),
  aiCurrentFile: null,
  setAICurrentFile: (path) => set({ aiCurrentFile: path }),
  aiFileProgress: null,
  setAIFileProgress: (index, total) => set({ aiFileProgress: { index, total } }),
  fileLiveWriting: {},
  setFileLiveWriting: (path, isLive) =>
    set((s) => ({
      fileLiveWriting: { ...s.fileLiveWriting, [path]: isLive },
      fileStatuses: {
        ...s.fileStatuses,
        [path]: {
          ...s.fileStatuses[path],
          isLiveWriting: isLive,
        },
      },
    })),

  // ─── File operations from chat ──────────────────────────────────────────
  createFile: (path, content, openAfter = false) =>
    set((s) => ({
      fileContents: { ...s.fileContents, [path]: content },
      fileStatuses: {
        ...s.fileStatuses,
        [path]: {
          ...s.fileStatuses[path],
          isNew: true,
          isAIGenerated: true,
          isModified: false,
        },
      },
      openFiles: s.openFiles.includes(path) ? s.openFiles : [...s.openFiles, path],
      activeFile: openAfter ? path : s.activeFile,
    })),

  appendToFile: (path, delta) =>
    set((s) => ({
      fileContents: { ...s.fileContents, [path]: (s.fileContents[path] ?? '') + delta },
      fileStatuses: {
        ...s.fileStatuses,
        [path]: {
          ...s.fileStatuses[path],
          isAIGenerated: true,
        },
      },
      recentlyModifiedFiles: [
        path,
        ...s.recentlyModifiedFiles.filter((p) => p !== path),
      ].slice(0, 10),
    })),

  // ─── Agent pipeline ─────────────────────────────────────────────────────
  agentSteps: [],

  addAgentStep: (step) =>
    set((s) => ({
      agentSteps: [
        ...s.agentSteps,
        {
          id: makeId(),
          status: 'running',
          ...step,
        },
      ],
    })),

  completeAgentStep: (agent, result) =>
    set((s) => ({
      agentSteps: s.agentSteps.map((step) =>
        step.agent === agent
          ? { ...step, status: 'done', result: result ?? step.result }
          : step
      ),
    })),

  clearAgentSteps: () => set({ agentSteps: [] }),
}));

// ─── PERSISTENCE (invisible, no UI coupling) ────────────────────────────────
// Only persists: openFiles, activeFile
// Does NOT persist: agent state, locks, activityLog, fileContents

const IDE_PERSIST_KEY = "atmos:ide:v1";

interface PersistedIDE {
  openFiles: string[];
  activeFile: string | null;
}

// Save on change (automatic, invisible)
let lastSaved = "";
useIDEStore.subscribe((state) => {
  const toSave: PersistedIDE = {
    openFiles: state.openFiles,
    activeFile: state.activeFile,
  };
  const json = JSON.stringify(toSave);
  if (json !== lastSaved) {
    lastSaved = json;
    try {
      localStorage.setItem(IDE_PERSIST_KEY, json);
    } catch {
      // Storage full or unavailable → ignore
    }
  }
});

// Restore on boot (call once at app start)
export function restoreIDEState(): void {
  try {
    const raw = localStorage.getItem(IDE_PERSIST_KEY);
    if (!raw) return;

    const saved = JSON.parse(raw) as PersistedIDE;
    if (!Array.isArray(saved.openFiles)) return;

    useIDEStore.setState({
      openFiles: saved.openFiles,
      activeFile: saved.activeFile ?? null,
    });
  } catch {
    // Corrupted state → ignore, start fresh
  }
}
