import { create } from 'zustand';
import { AIMessage, DiffChange } from '../types';

interface AIState {
    messages: AIMessage[];
    isProcessing: boolean;
    pendingDiff: DiffChange[] | null;
    pendingFilePath: string | null;
    addMessage: (message: Omit<AIMessage, 'id' | 'timestamp'>) => void;
    setProcessing: (processing: boolean) => void;
    setPendingDiff: (diff: DiffChange[] | null, filePath: string | null) => void;
    applyDiff: () => void;
    rejectDiff: () => void;
    clearMessages: () => void;
}

export const useAIStore = create<AIState>((set) => ({
    messages: [
        {
            id: '1',
            role: 'system',
            content: 'AI Assistant ready. How can I help you with your code today?',
            timestamp: Date.now(),
        },
    ],
    isProcessing: false,
    pendingDiff: null,
    pendingFilePath: null,
    addMessage: (message) =>
        set((state) => ({
            messages: [
                ...state.messages,
                {
                    ...message,
                    id: `msg-${Date.now()}`,
                    timestamp: Date.now(),
                },
            ],
        })),
    setProcessing: (processing) => set({ isProcessing: processing }),
    setPendingDiff: (diff, filePath) =>
        set({ pendingDiff: diff, pendingFilePath: filePath }),
    applyDiff: () =>
        set((state) => {
            // In production, this would apply the diff to the actual file
            console.log('Applying diff to', state.pendingFilePath);
            return { pendingDiff: null, pendingFilePath: null };
        }),
    rejectDiff: () => set({ pendingDiff: null, pendingFilePath: null }),
    clearMessages: () =>
        set({
            messages: [
                {
                    id: '1',
                    role: 'system',
                    content: 'AI Assistant ready. How can I help you with your code today?',
                    timestamp: Date.now(),
                },
            ],
        }),
}));