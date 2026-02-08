/**
 * IDE Store - AI-native state for project, intents, activity, and permission mode
 * Aligns with: controlled autonomy, human authority, intent visibility
 */

import { create } from 'zustand';
import type { DiffPlan } from '@/lib/diff';

// ─── Workspace Mode (empty = AI owns filesystem, project = AI + User) ────────

export type WorkspaceMode = 'empty' | 'project';

// ─── Project State ─────────────────────────────────────────────────────────

export type ProjectState = 'no_project' | 'loaded' | 'ai_running' | 'intent_review' | 'executing' | 'diff_review' | 'applying_diffs';

export interface ProjectInfo {
  id: string;
  name: string;
  path?: string;
}

// ─── AI Plan (Phase 2: planner output, no code/diffs) ───────────────────────

export interface Plan {
  summary: string;
  actions: {
    createFiles: string[];
    modifyFiles: string[];
    runCommands: string[];
  };
}

// ─── AI Intent (shown BEFORE changes) ───────────────────────────────────────

export interface AIIntentAction {
  type: 'read' | 'modify' | 'run' | 'create' | 'delete';
  target: string;
  detail?: string;
}

export interface AIIntent {
  id: string;
  createdAt: number;
  actions: AIIntentAction[];
  scope: string;
  summary?: string;
  status: 'pending' | 'approved' | 'rejected' | 'partial';
}

// ─── AI Activity (log for trust/debug) ───────────────────────────────────────

export interface AIActivityEntry {
  id: string;
  timestamp: number;
  action: string;
  detail?: string;
  success?: boolean;
}

// ─── Permission Mode ─────────────────────────────────────────────────────────

export type AIMode = 'assist' | 'apply_with_approval' | 'autonomous';

// ─── Diff Review (for when AI proposes edits) ────────────────────────────────

export interface PendingDiff {
  filePath: string;
  fileName: string;
  original: string;
  proposed: string;
  status: 'pending' | 'accepted' | 'rejected' | 'edited';
}

// ─── Store ──────────────────────────────────────────────────────────────────

interface IDEState {
  // Workspace mode — empty = fresh AI workspace, project = loaded/connected
  workspaceMode: WorkspaceMode;
  setWorkspaceMode: (mode: WorkspaceMode) => void;
  resetToEmptyWorkspace: () => void;

  // Project
  projectState: ProjectState;
  project: ProjectInfo | null;
  setProject: (p: ProjectInfo | null) => void;
  setProjectState: (s: ProjectState) => void;

  // AI Intent Panel (legacy: file_change flows)
  pendingIntent: AIIntent | null;
  showIntentPanel: boolean;
  setPendingIntent: (intent: AIIntent | null) => void;
  showIntent: (intent: AIIntent) => void;
  dismissIntent: () => void;
  approveIntent: () => void;
  rejectIntent: () => void;

  // AI Plan (Phase 2: intent preview before execution)
  pendingPlan: Plan | null;
  showPlanPanel: boolean;
  setPendingPlan: (plan: Plan | null) => void;
  clearPlanPanel: () => void;
  showPlan: (plan: Plan) => void;
  dismissPlan: () => void;
  approvePlan: () => void;
  rejectPlan: () => void;

  // Diff Review (Phase 4.3: preview before apply)
  pendingDiffPlan: DiffPlan | null;
  diffReviewFiles: Record<string, string>;
  showDiffReview: (diffPlan: DiffPlan, files: Record<string, string>) => void;
  dismissDiffReview: () => void;
  approveDiffReview: () => void;
  rejectDiffReview: () => void;

  // AI Activity Timeline
  activityLog: AIActivityEntry[];
  addActivity: (action: string, detail?: string, success?: boolean) => void;
  clearActivity: () => void;

  // Permission Mode
  aiMode: AIMode;
  setAIMode: (mode: AIMode) => void;

  // Pending diffs (for review surface)
  pendingDiffs: PendingDiff[];
  addPendingDiff: (diff: PendingDiff) => void;
  resolveDiff: (filePath: string, resolution: 'accepted' | 'rejected' | 'edited') => void;
  clearPendingDiffs: () => void;
}

const makeId = () => Math.random().toString(36).slice(2, 11);

export const useIDEStore = create<IDEState>((set, get) => ({
  workspaceMode: 'empty',
  setWorkspaceMode: (mode) => set({ workspaceMode: mode }),
  resetToEmptyWorkspace: () =>
    set({
      workspaceMode: 'empty',
      project: null,
      projectState: 'no_project',
    }),

  projectState: 'no_project',
  project: null,
  setProject: (p) =>
    set({
      project: p,
      projectState: p ? 'loaded' : 'no_project',
    }),
  setProjectState: (s) => set({ projectState: s }),

  pendingIntent: null,
  showIntentPanel: false,
  setPendingIntent: (intent) => set({ pendingIntent: intent }),
  showIntent: (intent) =>
    set({
      pendingIntent: intent,
      showIntentPanel: true,
    }),
  dismissIntent: () =>
    set({
      pendingIntent: null,
      showIntentPanel: false,
    }),
  approveIntent: () => {
    const { pendingIntent } = get();
    if (pendingIntent) {
      get().addActivity('Intent approved', pendingIntent.summary ?? JSON.stringify(pendingIntent.actions), true);
    }
    set({ pendingIntent: null, showIntentPanel: false });
  },
  rejectIntent: () => {
    const { pendingIntent } = get();
    if (pendingIntent) {
      get().addActivity('Intent rejected', pendingIntent.summary ?? 'User rejected', false);
    }
    set({ pendingIntent: null, showIntentPanel: false });
  },

  pendingPlan: null,
  showPlanPanel: false,
  setPendingPlan: (plan) => set({ pendingPlan: plan }),
  clearPlanPanel: () => set({ pendingPlan: null, showPlanPanel: false }),
  showPlan: (plan) =>
    set({
      pendingPlan: plan,
      showPlanPanel: true,
      projectState: 'intent_review',
    }),
  dismissPlan: () =>
    set({
      pendingPlan: null,
      showPlanPanel: false,
      projectState: get().project ? 'loaded' : 'no_project',
    }),
  approvePlan: () => {
    const { pendingPlan } = get();
    if (pendingPlan) {
      get().addActivity('Plan approved', pendingPlan.summary, true);
      // Phase 3: executor runs via IntentPreviewPanel onApprovePlan; this path unused
    }
    set({
      pendingPlan: null,
      showPlanPanel: false,
      projectState: get().project ? 'loaded' : 'no_project',
    });
  },
  rejectPlan: () => {
    const { pendingPlan } = get();
    if (pendingPlan) {
      get().addActivity('Plan rejected', pendingPlan.summary, false);
    }
    set({
      pendingPlan: null,
      showPlanPanel: false,
      projectState: get().project ? 'loaded' : 'no_project',
    });
  },

  pendingDiffPlan: null,
  diffReviewFiles: {},
  showDiffReview: (diffPlan, files) =>
    set({
      pendingDiffPlan: diffPlan,
      diffReviewFiles: files,
      projectState: 'diff_review',
    }),
  dismissDiffReview: () =>
    set({
      pendingDiffPlan: null,
      diffReviewFiles: {},
      projectState: get().project ? 'loaded' : 'no_project',
    }),
  approveDiffReview: () => {
    const { pendingDiffPlan } = get();
    if (pendingDiffPlan) {
      get().addActivity('Diffs approved', pendingDiffPlan.summary, true);
      // Phase 4.4: apply engine will run here
    }
    set({
      pendingDiffPlan: null,
      diffReviewFiles: {},
      projectState: get().project ? 'loaded' : 'no_project',
    });
  },
  rejectDiffReview: () => {
    const { pendingDiffPlan } = get();
    if (pendingDiffPlan) {
      get().addActivity('Diffs rejected', pendingDiffPlan.summary, false);
    }
    set({
      pendingDiffPlan: null,
      diffReviewFiles: {},
      projectState: get().project ? 'loaded' : 'no_project',
    });
  },

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
      ].slice(-100),
    })),
  clearActivity: () => set({ activityLog: [] }),

  aiMode: 'apply_with_approval',
  setAIMode: (mode) => set({ aiMode: mode }),

  pendingDiffs: [],
  addPendingDiff: (diff) =>
    set((s) => ({
      pendingDiffs: [...s.pendingDiffs.filter((d) => d.filePath !== diff.filePath), diff],
    })),
  resolveDiff: (filePath, resolution) =>
    set((s) => ({
      pendingDiffs: s.pendingDiffs.map((d) =>
        d.filePath === filePath ? { ...d, status: resolution } : d
      ),
    })),
  clearPendingDiffs: () => set({ pendingDiffs: [] }),
}));
