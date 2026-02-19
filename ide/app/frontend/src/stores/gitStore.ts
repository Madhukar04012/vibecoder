import { create } from 'zustand';
import { GitChange, GitBranch } from '../types';

interface GitState {
    currentBranch: string;
    branches: GitBranch[];
    changes: GitChange[];
    commits: Array<{ id: string; message: string; author: string; date: string }>;
    setCurrentBranch: (branch: string) => void;
    addChange: (change: GitChange) => void;
    stageChange: (path: string) => void;
    unstageChange: (path: string) => void;
    commit: (message: string) => void;
    createBranch: (name: string) => void;
    switchBranch: (name: string) => void;
}

export const useGitStore = create<GitState>((set) => ({
    currentBranch: 'main',
    branches: [
        { name: 'main', current: true },
        { name: 'develop', current: false },
        { name: 'feature/new-ui', current: false },
    ],
    changes: [
        { path: '/src/components/App.tsx', type: 'modified', staged: false },
        { path: '/src/utils/helpers.ts', type: 'modified', staged: false },
        { path: '/src/components/NewComponent.tsx', type: 'added', staged: false },
    ],
    commits: [
        { id: 'abc123', message: 'Initial commit', author: 'Developer', date: '2024-01-15' },
        { id: 'def456', message: 'Add new features', author: 'Developer', date: '2024-01-16' },
    ],
    setCurrentBranch: (branch) => set({ currentBranch: branch }),
    addChange: (change) =>
        set((state) => ({
            changes: [...state.changes, change],
        })),
    stageChange: (path) =>
        set((state) => ({
            changes: state.changes.map((change) =>
                change.path === path ? { ...change, staged: true } : change
            ),
        })),
    unstageChange: (path) =>
        set((state) => ({
            changes: state.changes.map((change) =>
                change.path === path ? { ...change, staged: false } : change
            ),
        })),
    commit: (message) =>
        set((state) => ({
            commits: [
                ...state.commits,
                {
                    id: Math.random().toString(36).substr(2, 9),
                    message,
                    author: 'Developer',
                    date: new Date().toISOString().split('T')[0],
                },
            ],
            changes: state.changes.filter((change) => !change.staged),
        })),
    createBranch: (name) =>
        set((state) => ({
            branches: [...state.branches, { name, current: false }],
        })),
    switchBranch: (name) =>
        set((state) => ({
            currentBranch: name,
            branches: state.branches.map((branch) => ({
                ...branch,
                current: branch.name === name,
            })),
        })),
}));