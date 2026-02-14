import { create } from 'zustand';
import { Terminal } from '../types';

interface TerminalState {
    terminals: Terminal[];
    activeTerminalId: string | null;
    createTerminal: (name?: string) => void;
    closeTerminal: (id: string) => void;
    setActiveTerminal: (id: string) => void;
    addOutput: (id: string, output: string) => void;
    clearTerminal: (id: string) => void;
}

export const useTerminalStore = create<TerminalState>((set) => ({
    terminals: [
        {
            id: 'terminal-1',
            name: 'Terminal 1',
            isActive: true,
            output: ['$ Welcome to Cloud IDE Terminal', '$ Ready for commands...'],
            cwd: '/workspace',
        },
    ],
    activeTerminalId: 'terminal-1',
    createTerminal: (name) =>
        set((state) => {
            const newTerminal: Terminal = {
                id: `terminal-${Date.now()}`,
                name: name || `Terminal ${state.terminals.length + 1}`,
                isActive: false,
                output: ['$ Welcome to Cloud IDE Terminal'],
                cwd: '/workspace',
            };
            return {
                terminals: [...state.terminals, newTerminal],
            };
        }),
    closeTerminal: (id) =>
        set((state) => {
            const newTerminals = state.terminals.filter((t) => t.id !== id);
            let newActiveId = state.activeTerminalId;
            if (state.activeTerminalId === id && newTerminals.length > 0) {
                newActiveId = newTerminals[0].id;
            }
            return {
                terminals: newTerminals,
                activeTerminalId: newActiveId,
            };
        }),
    setActiveTerminal: (id) => set({ activeTerminalId: id }),
    addOutput: (id, output) =>
        set((state) => ({
            terminals: state.terminals.map((t) =>
                t.id === id ? { ...t, output: [...t.output, output] } : t
            ),
        })),
    clearTerminal: (id) =>
        set((state) => ({
            terminals: state.terminals.map((t) =>
                t.id === id ? { ...t, output: [] } : t
            ),
        })),
}));