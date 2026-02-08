/**
 * Atmos AI Diff System
 * 
 * AI is READ-ONLY. It outputs DIFFS, not files.
 * User must APPROVE every change.
 * 
 * Flow:
 * 1. AI reads immutable snapshot
 * 2. AI outputs diff (before/after)
 * 3. User reviews in Diff Viewer
 * 4. User clicks Apply → Editor applies patch
 * 5. FileSystem.update() → version++
 */

import { EventBus, type DiffPayload, type AtmosEvent } from './event-bus';
import { VFS } from './virtual-fs';

// ─── Diff Types ─────────────────────────────────────────────────────────────

export interface AIDiff {
  id: string;
  filePath: string;
  before: string;
  after: string;
  agent: string;
  description: string;
  status: 'pending' | 'applied' | 'rejected';
  timestamp: number;
}

export interface AIDiffSet {
  id: string;
  prompt: string;
  diffs: AIDiff[];
  status: 'reviewing' | 'applied' | 'rejected' | 'partial';
  timestamp: number;
}

// ─── Diff Manager ───────────────────────────────────────────────────────────

let diffCounter = 0;
const makeId = () => `diff-${++diffCounter}-${Date.now().toString(36)}`;

class AIDiffManagerImpl {
  private pendingSets: Map<string, AIDiffSet> = new Map();
  private history: AIDiffSet[] = [];

  /** Create a diff set from AI output */
  createDiffSet(prompt: string, diffs: Omit<AIDiff, 'id' | 'status' | 'timestamp'>[]): AIDiffSet {
    const set: AIDiffSet = {
      id: makeId(),
      prompt,
      diffs: diffs.map((d) => ({
        ...d,
        id: makeId(),
        status: 'pending' as const,
        timestamp: Date.now(),
      })),
      status: 'reviewing',
      timestamp: Date.now(),
    };
    this.pendingSets.set(set.id, set);

    // Emit event for UI
    EventBus.emit('AI_DIFF_READY', set, 'ai-diff');
    return set;
  }

  /** Create a diff for a single new file (AI creating from scratch) */
  createNewFileDiff(filePath: string, content: string, agent: string, description: string): AIDiff {
    return {
      id: makeId(),
      filePath,
      before: '',
      after: content,
      agent,
      description,
      status: 'pending',
      timestamp: Date.now(),
    };
  }

  /** Apply a single diff */
  applyDiff(diffId: string, setId: string): boolean {
    const set = this.pendingSets.get(setId);
    if (!set) return false;

    const diff = set.diffs.find((d) => d.id === diffId);
    if (!diff || diff.status !== 'pending') return false;

    // Apply to VFS
    if (diff.before === '') {
      // New file
      VFS.create(diff.filePath, diff.after, true);
    } else {
      // Modify existing file
      VFS.update(diff.filePath, diff.after);
    }

    diff.status = 'applied';
    EventBus.emit('AI_DIFF_APPLIED', { filePath: diff.filePath, before: diff.before, after: diff.after } as DiffPayload, 'ai-diff');

    // Check if all diffs are resolved
    this.checkSetStatus(set);
    return true;
  }

  /** Reject a single diff */
  rejectDiff(diffId: string, setId: string): boolean {
    const set = this.pendingSets.get(setId);
    if (!set) return false;

    const diff = set.diffs.find((d) => d.id === diffId);
    if (!diff || diff.status !== 'pending') return false;

    diff.status = 'rejected';
    EventBus.emit('AI_DIFF_REJECTED', { filePath: diff.filePath } as DiffPayload, 'ai-diff');

    this.checkSetStatus(set);
    return true;
  }

  /** Apply ALL pending diffs in a set */
  applyAll(setId: string): void {
    const set = this.pendingSets.get(setId);
    if (!set) return;

    for (const diff of set.diffs) {
      if (diff.status === 'pending') {
        if (diff.before === '') {
          VFS.create(diff.filePath, diff.after, true);
        } else {
          VFS.update(diff.filePath, diff.after);
        }
        diff.status = 'applied';
        EventBus.emit('AI_DIFF_APPLIED', { filePath: diff.filePath, before: diff.before, after: diff.after } as DiffPayload, 'ai-diff');
      }
    }
    this.checkSetStatus(set);
  }

  /** Reject ALL pending diffs in a set */
  rejectAll(setId: string): void {
    const set = this.pendingSets.get(setId);
    if (!set) return;

    for (const diff of set.diffs) {
      if (diff.status === 'pending') {
        diff.status = 'rejected';
      }
    }
    set.status = 'rejected';
    this.pendingSets.delete(setId);
    this.history.push(set);
  }

  /** Get pending diff sets */
  getPending(): AIDiffSet[] {
    return Array.from(this.pendingSets.values());
  }

  /** Get history */
  getHistory(): AIDiffSet[] {
    return [...this.history];
  }

  private checkSetStatus(set: AIDiffSet): void {
    const allResolved = set.diffs.every((d) => d.status !== 'pending');
    if (allResolved) {
      const anyApplied = set.diffs.some((d) => d.status === 'applied');
      const anyRejected = set.diffs.some((d) => d.status === 'rejected');
      set.status = anyApplied && anyRejected ? 'partial' : anyApplied ? 'applied' : 'rejected';
      this.pendingSets.delete(set.id);
      this.history.push(set);
    }
  }

  /** Clear all */
  reset(): void {
    this.pendingSets.clear();
    this.history = [];
  }
}

// ─── Singleton ──────────────────────────────────────────────────────────────

export const AIDiffManager = new AIDiffManagerImpl();
