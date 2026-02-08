/**
 * IDE Store - Cursor/Replit Mode
 * Full state management for AI-powered IDE
 * Streaming support, file tracking, AI progress
 */

import { create } from 'zustand';

// ─── Types ──────────────────────────────────────────────────────────────────

export type WorkspaceMode = 'empty' | 'project';
export type ProjectState = 'no_project' | 'loaded' | 'ai_running';
export type AIStreamStatus = 'idle' | 'thinking' | 'generating' | 'streaming' | 'done' | 'error';

export interface ProjectInfo {
  id: string;
  name: string;
  path?: string;
}

export interface AIActivityEntry {
  id: string;
  timestamp: number;
  action: string;
  detail?: string;
  success?: boolean;
  type?: 'file_create' | 'file_modify' | 'thinking' | 'message' | 'command' | 'error';
}

export type TerminalLineType = 'command' | 'stdout' | 'stderr';
export interface TerminalLine {
  type: TerminalLineType;
  text: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  isStreaming?: boolean;
  files?: { path: string; status: 'pending' | 'generating' | 'done' }[];
}

export interface FileStatus {
  isNew: boolean;
  isModified: boolean;
  isAIGenerated: boolean;
  isLiveWriting: boolean;
  lastModified: number;
}

export interface AgentStep {
  id: string;
  agent: string;
  name: string;
  icon: string;
  description: string;
  status: 'running' | 'done';
  result?: string;
  timestamp: number;
}

// ─── Store Interface ────────────────────────────────────────────────────────

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
  createFile: (path: string, content: string, aiGenerated?: boolean) => void;
  appendToFile: (path: string, delta: string) => void;
  setFileLiveWriting: (path: string, writing: boolean) => void;
  deleteFile: (path: string) => void;
  renameFile: (oldPath: string, newPath: string) => void;

  // Agent pipeline steps
  agentSteps: AgentStep[];
  addAgentStep: (step: Omit<AgentStep, 'id' | 'timestamp' | 'status'>) => void;
  completeAgentStep: (agent: string, result: string) => void;
  clearAgentSteps: () => void;

  // Workspace
  workspaceMode: WorkspaceMode;
  setWorkspaceMode: (mode: WorkspaceMode) => void;
  resetToEmptyWorkspace: () => void;

  // Project
  projectState: ProjectState;
  project: ProjectInfo | null;
  setProject: (p: ProjectInfo | null) => void;
  setProjectState: (s: ProjectState) => void;

  // AI Stream state
  aiStatus: AIStreamStatus;
  aiCurrentFile: string | null;
  aiFileProgress: { current: number; total: number };
  setAIStatus: (status: AIStreamStatus) => void;
  setAICurrentFile: (file: string | null) => void;
  setAIFileProgress: (current: number, total: number) => void;

  // Chat messages
  chatMessages: ChatMessage[];
  addChatMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  updateLastAssistantMessage: (content: string) => void;
  appendToLastAssistantMessage: (token: string) => void;
  clearChat: () => void;

  // Activity log
  activityLog: AIActivityEntry[];
  addActivity: (action: string, detail?: string, success?: boolean, type?: AIActivityEntry['type']) => void;
  clearActivity: () => void;

  // Workspace awareness
  recentlyOpenedFiles: string[];
  recentlyModifiedFiles: string[];
  activeContextFiles: string[];
  markOpened: (path: string) => void;
  markModified: (path: string) => void;
  setActiveContext: (paths: string[]) => void;

  // Terminal output
  terminalLines: TerminalLine[];
  appendTerminalLine: (text: string, type?: TerminalLineType) => void;
  clearTerminal: () => void;
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
          ? next.length ? next[next.length - 1] : null
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
          ...(state.fileStatuses[path] || { isNew: false, isAIGenerated: false }),
          isModified: true,
          lastModified: Date.now(),
        },
      },
    })),

  createFile: (path, content, aiGenerated = false) => {
    const { openFiles } = get();
    set((state) => ({
      fileContents: { ...state.fileContents, [path]: content },
      fileStatuses: {
        ...state.fileStatuses,
        [path]: {
          isNew: true,
          isModified: false,
          isAIGenerated: aiGenerated,
          isLiveWriting: false,
          lastModified: Date.now(),
        },
      },
      openFiles: openFiles.includes(path) ? openFiles : [...openFiles, path],
      workspaceMode: 'project' as WorkspaceMode,
    }));
  },

  appendToFile: (path, delta) =>
    set((state) => ({
      fileContents: {
        ...state.fileContents,
        [path]: (state.fileContents[path] ?? '') + delta,
      },
    })),

  setFileLiveWriting: (path, writing) =>
    set((state) => ({
      fileStatuses: {
        ...state.fileStatuses,
        [path]: {
          ...(state.fileStatuses[path] || { isNew: true, isModified: false, isAIGenerated: true, lastModified: Date.now() }),
          isLiveWriting: writing,
        },
      },
    })),

  deleteFile: (path) => {
    const { openFiles, activeFile, fileContents, fileStatuses } = get();
    const newContents = { ...fileContents };
    delete newContents[path];
    const newStatuses = { ...fileStatuses };
    delete newStatuses[path];
    const newOpen = openFiles.filter((f) => f !== path);
    set({
      fileContents: newContents,
      fileStatuses: newStatuses,
      openFiles: newOpen,
      activeFile: path === activeFile ? (newOpen[newOpen.length - 1] || null) : activeFile,
    });
  },

  renameFile: (oldPath, newPath) => {
    const { fileContents, fileStatuses, openFiles, activeFile } = get();
    const content = fileContents[oldPath] ?? '';
    const status = fileStatuses[oldPath];
    const newContents = { ...fileContents };
    delete newContents[oldPath];
    newContents[newPath] = content;
    const newStatuses = { ...fileStatuses };
    delete newStatuses[oldPath];
    if (status) newStatuses[newPath] = status;
    set({
      fileContents: newContents,
      fileStatuses: newStatuses,
      openFiles: openFiles.map((f) => (f === oldPath ? newPath : f)),
      activeFile: activeFile === oldPath ? newPath : activeFile,
    });
  },

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
      fileStatuses: {},
      chatMessages: [],
      agentSteps: [],
      aiStatus: 'idle',
      aiCurrentFile: null,
      aiFileProgress: { current: 0, total: 0 },
    }),

  // ─── Project ──────────────────────────────────────────────────────────────
  projectState: 'no_project',
  project: null,
  setProject: (p) => set({ project: p, projectState: p ? 'loaded' : 'no_project' }),
  setProjectState: (s) => set({ projectState: s }),

  // ─── AI Stream State ──────────────────────────────────────────────────────
  aiStatus: 'idle',
  aiCurrentFile: null,
  aiFileProgress: { current: 0, total: 0 },
  setAIStatus: (status) => set({ aiStatus: status }),
  setAICurrentFile: (file) => set({ aiCurrentFile: file }),
  setAIFileProgress: (current, total) => set({ aiFileProgress: { current, total } }),

  // ─── Agent Pipeline Steps ──────────────────────────────────────────────────
  agentSteps: [],

  addAgentStep: (step) =>
    set((s) => ({
      agentSteps: [
        ...s.agentSteps,
        { ...step, id: makeId(), timestamp: Date.now(), status: 'running' as const },
      ],
    })),

  completeAgentStep: (agent, result) =>
    set((s) => ({
      agentSteps: s.agentSteps.map((step) =>
        step.agent === agent && step.status === 'running'
          ? { ...step, status: 'done' as const, result }
          : step
      ),
    })),

  clearAgentSteps: () => set({ agentSteps: [] }),

  // ─── Chat Messages ────────────────────────────────────────────────────────
  chatMessages: [],

  addChatMessage: (msg) =>
    set((s) => ({
      chatMessages: [
        ...s.chatMessages,
        { ...msg, id: makeId(), timestamp: Date.now() },
      ],
    })),

  updateLastAssistantMessage: (content) =>
    set((s) => {
      const msgs = [...s.chatMessages];
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === 'assistant') {
          msgs[i] = { ...msgs[i], content, isStreaming: false };
          break;
        }
      }
      return { chatMessages: msgs };
    }),

  appendToLastAssistantMessage: (token) =>
    set((s) => {
      const msgs = [...s.chatMessages];
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === 'assistant') {
          msgs[i] = { ...msgs[i], content: msgs[i].content + token };
          break;
        }
      }
      return { chatMessages: msgs };
    }),

  clearChat: () => set({ chatMessages: [] }),

  // ─── Activity Log ─────────────────────────────────────────────────────────
  activityLog: [],

  addActivity: (action, detail, success, type) =>
    set((s) => ({
      activityLog: [
        ...s.activityLog,
        { id: makeId(), timestamp: Date.now(), action, detail, success, type },
      ].slice(-100),
    })),

  clearActivity: () => set({ activityLog: [] }),

  // ─── Workspace Awareness ──────────────────────────────────────────────────
  recentlyOpenedFiles: [],
  recentlyModifiedFiles: [],
  activeContextFiles: [],

  markOpened: (path) =>
    set((s) => ({
      recentlyOpenedFiles: [path, ...s.recentlyOpenedFiles.filter((p) => p !== path)].slice(0, 10),
    })),

  markModified: (path) =>
    set((s) => ({
      recentlyModifiedFiles: [path, ...s.recentlyModifiedFiles.filter((p) => p !== path)].slice(0, 10),
    })),

  setActiveContext: (paths) =>
    set({ activeContextFiles: Array.from(new Set(paths.filter(Boolean))).slice(0, 10) }),

  // ─── Terminal ─────────────────────────────────────────────────────────────
  terminalLines: [],

  appendTerminalLine: (text, type = 'stdout') =>
    set((s) => ({
      terminalLines: [...s.terminalLines, { type, text }].slice(-500),
    })),

  clearTerminal: () => set({ terminalLines: [] }),
}));

// ─── Persistence ────────────────────────────────────────────────────────────

const IDE_PERSIST_KEY = 'vibecober:ide:v2';

interface PersistedIDE {
  openFiles: string[];
  activeFile: string | null;
  fileContents: Record<string, string>;
  fileStatuses: Record<string, FileStatus>;
  chatMessages: ChatMessage[];
}

let lastSaved = '';
useIDEStore.subscribe((state) => {
  const toSave: PersistedIDE = {
    openFiles: state.openFiles,
    activeFile: state.activeFile,
    fileContents: state.fileContents,
    fileStatuses: state.fileStatuses,
    chatMessages: state.chatMessages.slice(-50),
  };
  const json = JSON.stringify(toSave);
  if (json !== lastSaved) {
    lastSaved = json;
    try {
      localStorage.setItem(IDE_PERSIST_KEY, json);
    } catch {
      // Storage full → ignore
    }
  }
});

export function restoreIDEState(): void {
  try {
    const raw = localStorage.getItem(IDE_PERSIST_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw) as PersistedIDE;
    if (!Array.isArray(saved.openFiles)) return;

    // Clean up streaming state from messages (in case page was closed during stream)
    const messages = (saved.chatMessages ?? []).map((m) => ({
      ...m,
      isStreaming: false,
    }));

    const fileContents = saved.fileContents ?? {};
    const hasFiles = Object.keys(fileContents).length > 0;

    useIDEStore.setState({
      openFiles: saved.openFiles,
      activeFile: saved.activeFile ?? null,
      fileContents,
      fileStatuses: saved.fileStatuses ?? {},
      chatMessages: messages,
      workspaceMode: hasFiles ? 'project' : 'empty',
      projectState: hasFiles ? 'loaded' : 'no_project',
      project: hasFiles ? { id: 'restored', name: 'My Project' } : null,
    });
  } catch {
    // Corrupted → start fresh
  }
}
