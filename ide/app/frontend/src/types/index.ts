export interface FileNode {
    id: string;
    name: string;
    type: 'file' | 'folder';
    path: string;
    children?: FileNode[];
    isOpen?: boolean;
    content?: string;
    language?: string;
    modified?: boolean;
}

export interface EditorTab {
    id: string;
    fileId: string;
    title: string;
    path: string;
    content: string;
    language: string;
    isDirty: boolean;
    isActive: boolean;
}

export interface GitChange {
    path: string;
    type: 'modified' | 'added' | 'deleted' | 'renamed';
    staged: boolean;
}

export interface GitBranch {
    name: string;
    current: boolean;
    remote?: string;
}

export interface AIMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: number;
    toolCalls?: ToolCall[];
}

export interface ToolCall {
    id: string;
    name: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    input: any;
    output?: any;
}

export interface DiffChange {
    type: 'add' | 'remove' | 'modify';
    lineNumber: number;
    content: string;
    oldContent?: string;
}

export interface Terminal {
    id: string;
    name: string;
    isActive: boolean;
    output: string[];
    cwd: string;
}

export interface Problem {
    severity: 'error' | 'warning' | 'info';
    message: string;
    file: string;
    line: number;
    column: number;
}

export type ActivityView = 'explorer' | 'search' | 'git' | 'extensions' | 'ai' | 'terminal' | 'settings';

export type Theme = 'dark' | 'light';

export interface KeyboardShortcut {
    key: string;
    ctrl?: boolean;
    shift?: boolean;
    alt?: boolean;
    meta?: boolean;
    action: () => void;
    description: string;
}