import { create } from 'zustand';
import { RuntimeEngine } from './runtime';

export type IDEMode = 'idle' | 'running' | 'error';

export interface AuthUser {
    id?: string;
    email?: string;
    name?: string | null;
    created_at?: string;
}

interface IDEStore {
    mode: IDEMode;
    activeFile: string | null;  // Can be null if no tabs open
    openFiles: string[];        // List of open file paths
    locked: boolean;
    console: string[];
    errorFile?: string;

    accessToken: string | null;
    currentUser: AuthUser | null;

    isLocal: boolean;
    cloudEnabled: boolean;
    githubConnected: boolean;
    dbConnected: boolean;
    // Git State
    gitChanges: number;
    gitStatus: 'clean' | 'modified' | 'syncing';

    run: () => Promise<void>;
    appendLog: (line: string) => void;
    setError: (file: string, message: string) => void;
    reset: () => void;

    // Tab Actions
    openFile: (file: string) => void;
    closeFile: (file: string) => void;
    setActiveFile: (file: string) => void;

    toggleCloud: (enabled: boolean) => void;
    toggleDB: (connected: boolean) => void;
    toggleGitHub: (connected: boolean) => void;

    setAuth: (accessToken: string | null, user: AuthUser | null) => void;

    // Git Actions
    setFileModified: () => void;
    syncGit: () => Promise<void>;
}

export const useIDE = create<IDEStore>((set, get) => ({
    mode: 'idle',
    activeFile: 'backend/main.py',
    openFiles: ['backend/main.py'], // Start with one file open
    locked: false,
    console: [],

    accessToken: null,
    currentUser: null,

    isLocal: true,
    cloudEnabled: false,
    githubConnected: false,
    dbConnected: false,

    gitChanges: 0,
    gitStatus: 'clean',

    appendLog: (line) =>
        set((s) => ({ console: [...s.console, line] })),

    // Tab Logic
    openFile: (file) => {
        const { openFiles } = get();
        if (!openFiles.includes(file)) {
            set({ openFiles: [...openFiles, file], activeFile: file });
        } else {
            set({ activeFile: file });
        }
    },

    closeFile: (file) => {
        const { openFiles, activeFile } = get();
        const newOpenFiles = openFiles.filter(f => f !== file);

        // Determine new active file if we closed the active one
        let newActiveFile = activeFile;
        if (activeFile === file) {
            newActiveFile = newOpenFiles.length > 0 ? newOpenFiles[newOpenFiles.length - 1] : null;
        }

        set({ openFiles: newOpenFiles, activeFile: newActiveFile });
    },

    setActiveFile: (file) => set({ activeFile: file }),

    toggleCloud: (enabled) => set({ cloudEnabled: enabled, isLocal: !enabled }),
    toggleDB: (connected) => set({ dbConnected: connected }),
    toggleGitHub: (connected) => set({ githubConnected: connected }),

    setAuth: (accessToken, user) => set({ accessToken, currentUser: user }),

    setFileModified: () => {
        const { gitStatus } = get();
        if (gitStatus !== 'modified') {
            set({ gitStatus: 'modified', gitChanges: get().gitChanges + 1 });
        }
    },

    syncGit: async () => {
        const { githubConnected, gitChanges } = get();
        if (!githubConnected || gitChanges === 0) return;

        set({ gitStatus: 'syncing' });
        get().appendLog(`git: syncing ${gitChanges} changes...`);

        await new Promise(r => setTimeout(r, 1500));

        set({ gitStatus: 'clean', gitChanges: 0 });
        get().appendLog('git: sync complete (main)');
    },

    run: async () => {
        const state = get();
        if (state.mode === 'running' || !state.activeFile) return;

        set({ mode: 'running', locked: true, console: [] });

        try {
            const result = await RuntimeEngine.execute(
                {
                    file: state.activeFile,
                    isLocal: state.isLocal,
                    cloudEnabled: state.cloudEnabled,
                    dbConnected: state.dbConnected,
                    githubConnected: state.githubConnected
                },
                (log: string) => get().appendLog(log)
            );

            if (result.success) {
                set({ mode: 'idle', locked: false });
            } else {
                set({
                    mode: 'error',
                    locked: false,
                    errorFile: state.activeFile
                });
            }
        } catch {
            set({ mode: 'error', locked: false });
            get().appendLog(`CRITICAL ERROR: Runtime crashed`);
        }
    },

    setError: (file, message) =>
        set({
            mode: 'error',
            errorFile: file,
            locked: false,
            console: [...get().console, `❌ ${message}`],
        }),

    reset: () =>
        set({ mode: 'idle', locked: false, errorFile: undefined }),
}));
