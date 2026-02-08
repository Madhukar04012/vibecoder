/**
 * Atmos Virtual FileSystem — Versioned, snapshot-based
 * 
 * Rules:
 * - Editor reads/writes here
 * - AI never touches this directly (reads snapshots only)
 * - Execution reads snapshots
 * - Preview never reads files
 * - Every write increments version
 */

import { EventBus, type FilePayload } from './event-bus';

// ─── File Node ──────────────────────────────────────────────────────────────

export interface FileNode {
  path: string;
  content: string;
  version: number;
  createdAt: number;
  updatedAt: number;
  isAIGenerated: boolean;
}

// ─── Immutable Snapshot (what AI sees) ──────────────────────────────────────

export interface FileSystemSnapshot {
  files: Record<string, string>;    // path → content
  versions: Record<string, number>; // path → version
  timestamp: number;
  projectName: string;
}

// ─── AI Context Snapshot ────────────────────────────────────────────────────

export interface AIContextSnapshot {
  activeFile: string | null;
  selectedCode: string | null;
  dependencyFiles: Record<string, string>;
  projectTree: string[];
  timestamp: number;
}

// ─── Virtual FileSystem ─────────────────────────────────────────────────────

class VirtualFileSystemImpl {
  private files: Map<string, FileNode> = new Map();
  private projectName: string = 'New Project';

  /** Create a new file */
  create(path: string, content: string, aiGenerated = false): FileNode {
    const node: FileNode = {
      path,
      content,
      version: 1,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      isAIGenerated: aiGenerated,
    };
    this.files.set(path, node);
    EventBus.emit('FILE_CREATED', { path, content, version: 1 } as FilePayload, 'vfs');
    return node;
  }

  /** Update file content (version++) */
  update(path: string, content: string): FileNode | null {
    const existing = this.files.get(path);
    if (!existing) return null;
    const updated: FileNode = {
      ...existing,
      content,
      version: existing.version + 1,
      updatedAt: Date.now(),
    };
    this.files.set(path, updated);
    EventBus.emit('FILE_UPDATED', { path, content, version: updated.version } as FilePayload, 'vfs');
    return updated;
  }

  /** Delete a file */
  delete(path: string): boolean {
    if (!this.files.has(path)) return false;
    this.files.delete(path);
    EventBus.emit('FILE_DELETED', { path } as FilePayload, 'vfs');
    return true;
  }

  /** Rename a file */
  rename(oldPath: string, newPath: string): FileNode | null {
    const node = this.files.get(oldPath);
    if (!node) return null;
    const renamed: FileNode = { ...node, path: newPath, updatedAt: Date.now() };
    this.files.delete(oldPath);
    this.files.set(newPath, renamed);
    EventBus.emit('FILE_RENAMED', { path: newPath, content: oldPath } as FilePayload, 'vfs');
    return renamed;
  }

  /** Read a file */
  read(path: string): FileNode | undefined {
    return this.files.get(path);
  }

  /** Check if file exists */
  exists(path: string): boolean {
    return this.files.has(path);
  }

  /** Get all file paths */
  listPaths(): string[] {
    return Array.from(this.files.keys()).sort();
  }

  /** Get all file nodes */
  listFiles(): FileNode[] {
    return Array.from(this.files.values());
  }

  /** Get file count */
  count(): number {
    return this.files.size;
  }

  /** Append content to a file (for live writing) */
  append(path: string, delta: string): FileNode | null {
    const existing = this.files.get(path);
    if (!existing) {
      // Auto-create if doesn't exist
      return this.create(path, delta, true);
    }
    const updated: FileNode = {
      ...existing,
      content: existing.content + delta,
      updatedAt: Date.now(),
      // Don't increment version during live writing (bulk update)
    };
    this.files.set(path, updated);
    // No event for append — handled by AI_FILE_DELTA
    return updated;
  }

  // ─── Snapshot System (Immutable) ──────────────────────────────────────────

  /** Take an immutable snapshot of the entire filesystem */
  snapshot(): FileSystemSnapshot {
    const files: Record<string, string> = {};
    const versions: Record<string, number> = {};
    for (const [path, node] of this.files) {
      files[path] = node.content;
      versions[path] = node.version;
    }
    return Object.freeze({
      files,
      versions,
      timestamp: Date.now(),
      projectName: this.projectName,
    });
  }

  /** Build an AI context snapshot (what AI sees) */
  aiSnapshot(activeFile: string | null, selectedCode: string | null = null): AIContextSnapshot {
    const allFiles: Record<string, string> = {};
    for (const [path, node] of this.files) {
      allFiles[path] = node.content;
    }
    return Object.freeze({
      activeFile,
      selectedCode,
      dependencyFiles: allFiles,
      projectTree: this.listPaths(),
      timestamp: Date.now(),
    });
  }

  // ─── Project Management ───────────────────────────────────────────────────

  setProjectName(name: string): void {
    this.projectName = name;
  }

  getProjectName(): string {
    return this.projectName;
  }

  /** Clear all files */
  reset(): void {
    this.files.clear();
    this.projectName = 'New Project';
    EventBus.emit('PROJECT_RESET', {}, 'vfs');
  }

  /** Bulk load files (from persistence or AI generation) */
  loadFiles(files: Record<string, string>, aiGenerated = false): void {
    for (const [path, content] of Object.entries(files)) {
      this.create(path, content, aiGenerated);
    }
  }

  /** Export to plain object (for persistence) */
  toJSON(): Record<string, { content: string; version: number; isAIGenerated: boolean }> {
    const result: Record<string, { content: string; version: number; isAIGenerated: boolean }> = {};
    for (const [path, node] of this.files) {
      result[path] = { content: node.content, version: node.version, isAIGenerated: node.isAIGenerated };
    }
    return result;
  }

  /** Import from plain object (from persistence) */
  fromJSON(data: Record<string, { content: string; version: number; isAIGenerated: boolean }>): void {
    this.files.clear();
    for (const [path, info] of Object.entries(data)) {
      this.files.set(path, {
        path,
        content: info.content,
        version: info.version,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        isAIGenerated: info.isAIGenerated,
      });
    }
  }
}

// ─── Singleton ──────────────────────────────────────────────────────────────

export const VFS = new VirtualFileSystemImpl();
