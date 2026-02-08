/**
 * IDE state persistence — localStorage, no UI
 * Restores last file, tabs, view mode, cursor position
 */

const KEY = 'vibecober-novaide-state';

export interface CursorState {
  line: number;
  column: number;
  scrollTop: number;
}

export interface IDEState {
  projectId: string;
  activeTab: string;
  openTabs: { path: string; name: string }[];
  viewMode: 'editor' | 'viewer' | 'terminal';
  sidebarVisible: boolean;
  cursorStates: Record<string, CursorState>;
}

export function loadIDEState(projectId: string): IDEState | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as IDEState;
    if (parsed.projectId !== projectId) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function saveIDEState(state: IDEState): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    // quota exceeded or disabled
  }
}
