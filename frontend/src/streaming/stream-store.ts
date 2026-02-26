/**
 * Stream Store — Cinematic AI execution state
 *
 * Tracks:
 *  - Phase progression (understanding → planning → … → completed)
 *  - Phase progress (0–1) and checkpoints
 *  - Agent presence (idle / thinking / working / done)
 *  - Streaming mode (simple / developer / debug)
 *  - File batches (grouped file generation tree — dev/debug modes)
 */

import { create } from 'zustand';
import { type Phase, PHASE_PROGRESS } from './phase-engine';

// ─── Types ────────────────────────────────────────────────────────────────────

export type AgentStatus = 'idle' | 'thinking' | 'working' | 'reviewing' | 'done';
export type StreamMode   = 'simple' | 'developer' | 'debug';
export type { Phase };

export interface AgentPresence {
  id:     string;
  name:   string;
  avatar: string;
  color:  string;
  status: AgentStatus;
  model?: string;
}

export interface Checkpoint {
  id:     string;
  label:  string;
  status: 'pending' | 'done';
}

/** Used by atmos-state for narrative feed. */
export interface NarrativeItem {
  id:   string;
  text: string;
  type: 'check' | 'info' | 'warn';
}

export interface FileBatch {
  group:     string;
  files:     string[];
  doneCount: number;
}

// ─── Backend → Roster ID mapping ─────────────────────────────────────────────

export function toRosterId(backendId: string): string | null {
  const map: Record<string, string> = {
    planner:       'team_lead',
    pm:            'pm',
    architect:     'architect',
    db_schema:     'architect',
    auth:          'engineer',
    coder:         'engineer',
    engineer:      'engineer',
    code_reviewer: 'qa',
    tester:        'qa',
    qa:            'qa',
    deployer:      'devops',
    devops:        'devops',
    team_lead:     'team_lead',
  };
  return map[backendId] ?? null;
}

// ─── Initial Roster ───────────────────────────────────────────────────────────

const ROSTER: AgentPresence[] = [
  { id: 'team_lead', name: 'Team Lead',  avatar: 'TL', color: '#e8a245', status: 'idle', model: 'Nemotron 49B' },
  { id: 'pm',        name: 'PM',         avatar: 'PM', color: '#a78bfa', status: 'idle' },
  { id: 'architect', name: 'Architect',  avatar: 'AR', color: '#38bdf8', status: 'idle', model: 'Llama 3.3 70B' },
  { id: 'engineer',  name: 'Engineer',   avatar: 'EN', color: '#34d399', status: 'idle', model: 'Devstral 123B' },
  { id: 'qa',        name: 'QA',         avatar: 'QA', color: '#fb7185', status: 'idle', model: 'QWQ 32B' },
  { id: 'devops',    name: 'DevOps',     avatar: 'DO', color: '#c084fc', status: 'idle' },
];

// ─── Helper: derive group name from file path ─────────────────────────────────

function groupKey(path: string): string {
  const parts = path.split('/');
  if (parts.length > 1) return parts[0];
  const ext = path.split('.').pop()?.toLowerCase() ?? '';
  if (ext === 'py')  return 'Python';
  if (ext === 'ts' || ext === 'tsx' || ext === 'js' || ext === 'jsx') return 'JavaScript';
  if (ext === 'yml' || ext === 'yaml') return 'Config';
  return 'Root';
}

// ─── Store ────────────────────────────────────────────────────────────────────

interface StreamStore {
  // ── Phase engine ──────────────────────────────────────────────────────────
  phase:       Phase;
  progress:    number;          // 0–1
  checkpoints: Checkpoint[];

  setPhase:                  (phase: Phase) => void;
  addCheckpoint:             (label: string) => string;  // returns the new checkpoint id
  completeCheckpoint:        (id: string) => void;
  completeLastPendingCheckpoint: () => void;
  setProgress:               (value: number) => void;
  bumpProgress:              (delta: number, cap?: number) => void;

  // ── Agent presence ────────────────────────────────────────────────────────
  agents:         AgentPresence[];
  setAgentStatus: (rosterId: string, status: AgentStatus) => void;

  // ── Mode toggle ───────────────────────────────────────────────────────────
  mode:    StreamMode;
  setMode: (m: StreamMode) => void;

  // ── File batches (dev/debug) ───────────────────────────────────────────────
  fileBatches: FileBatch[];
  trackFile:   (path: string) => void;
  markFileDone:(path: string) => void;

  narrativeItems:   NarrativeItem[];
  addNarrativeItem: (text: string, type?: NarrativeItem['type']) => void;

  // ── Live agent text (streams inside PhaseBlock) ────────────────────────────
  liveText:       string;
  isAgentActive:  boolean;
  agentName:      string;         // e.g. "Engineer"
  setLiveText:    (text: string, agentName?: string) => void;
  appendLiveText: (token: string) => void;
  setAgentActive: (active: boolean) => void;

  reset: () => void;
}

export const useStreamStore = create<StreamStore>((set) => ({
  // ── Phase engine ──────────────────────────────────────────────────────────
  phase:       'understanding',
  progress:    0,
  checkpoints: [],

  setPhase: (phase) => {
    // 400ms delay for cinematic pacing between phase transitions
    setTimeout(() => {
      set({
        phase,
        progress:    PHASE_PROGRESS[phase] ?? 0,
        checkpoints: [],
      });
    }, 400);
  },

  addCheckpoint: (label) => {
    const id = crypto.randomUUID();
    set(s => ({
      checkpoints: [
        ...s.checkpoints,
        { id, label, status: 'pending' },
      ],
    }));
    return id;
  },

  completeCheckpoint: (id) =>
    set(s => ({
      checkpoints: s.checkpoints.map(cp =>
        cp.id === id ? { ...cp, status: 'done' } : cp
      ),
    })),

  completeLastPendingCheckpoint: () =>
    set(s => {
      const lastPending = [...s.checkpoints].reverse().find(cp => cp.status === 'pending');
      if (!lastPending) return s;
      return {
        checkpoints: s.checkpoints.map(cp =>
          cp.id === lastPending.id ? { ...cp, status: 'done' } : cp
        ),
      };
    }),

  setProgress: (value) => set({ progress: Math.min(1, Math.max(0, value)) }),

  bumpProgress: (delta, cap = 0.95) =>
    set(s => ({ progress: Math.min(cap, s.progress + delta) })),

  // ── Agent presence ────────────────────────────────────────────────────────
  agents: ROSTER.map(a => ({ ...a })),

  setAgentStatus: (rosterId, status) =>
    set(s => ({
      agents: s.agents.map(a => a.id === rosterId ? { ...a, status } : a),
    })),

  // ── Mode toggle ───────────────────────────────────────────────────────────
  mode:    'simple',
  setMode: (mode) => set({ mode }),

  // ── File batches ──────────────────────────────────────────────────────────
  fileBatches: [],

  trackFile: (path) =>
    set(s => {
      const key = groupKey(path);
      const existing = s.fileBatches.find(b => b.group === key);
      if (existing) {
        if (existing.files.includes(path)) return s;
        return {
          fileBatches: s.fileBatches.map(b =>
            b.group === key ? { ...b, files: [...b.files, path] } : b
          ),
        };
      }
      return {
        fileBatches: [...s.fileBatches, { group: key, files: [path], doneCount: 0 }],
      };
    }),

  markFileDone: (path) =>
    set(s => {
      const key = groupKey(path);
      return {
        fileBatches: s.fileBatches.map(b =>
          b.group === key ? { ...b, doneCount: Math.min(b.doneCount + 1, b.files.length) } : b
        ),
      };
    }),

  // ── Narrative (deprecated — kept for backward-compat) ────────────────────
  narrativeItems: [],
  addNarrativeItem: (text, type = 'check') =>
    set(s => ({
      narrativeItems: [
        ...s.narrativeItems,
        { id: Math.random().toString(36).slice(2, 9), text, type },
      ],
    })),

  // ── Live agent text (streams directly inside PhaseBlock) ─────────────────
  liveText:      '',
  isAgentActive: false,
  agentName:     '',

  setLiveText:    (text, name = '') => set({ liveText: text, agentName: name, isAgentActive: true }),
  appendLiveText: (token) => set(s => ({ liveText: s.liveText + token })),
  setAgentActive: (active) => set({ isAgentActive: active }),

  // ── Reset (called after pipeline completes) ───────────────────────────────
  reset: () =>
    set({
      phase:          'understanding',
      progress:       0,
      checkpoints:    [],
      agents:         ROSTER.map(a => ({ ...a })),
      fileBatches:    [],
      narrativeItems: [],
      liveText:       '',
      isAgentActive:  false,
      agentName:      '',
    }),
}));
