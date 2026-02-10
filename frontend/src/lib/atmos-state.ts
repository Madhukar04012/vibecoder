/**
 * ATMOS State Machine — AI-Only Operation Mode
 * 
 * Core Law: User expresses intent. AI decides everything else. UI only reflects reality.
 * 
 * States:
 *   IDLE → INTERPRETING → GENERATING → BUILDING → RUNNING → LIVE
 *                                                             ↓
 *                                          ERROR_FIXING ←────←
 *                                               ↓
 *                                          (auto-retry → BUILDING)
 */

import { create } from 'zustand';
import { EventBus } from './event-bus';

// ─── ATMOS Phases ───────────────────────────────────────────────────────────

export type AtmosPhase =
    | 'idle'
    | 'interpreting'
    | 'generating'
    | 'building'
    | 'running'
    | 'live'
    | 'error_fixing';

// Valid transitions
const VALID_TRANSITIONS: Record<AtmosPhase, AtmosPhase[]> = {
    idle: ['interpreting'],
    interpreting: ['generating', 'error_fixing', 'idle'],
    generating: ['building', 'error_fixing', 'idle'],
    building: ['running', 'error_fixing', 'idle'],
    running: ['live', 'error_fixing', 'idle'],
    live: ['interpreting', 'idle'],   // user sends new intent
    error_fixing: ['building', 'generating', 'idle'],  // retry or give up
};

// ─── Phase Display ──────────────────────────────────────────────────────────

export const PHASE_DISPLAY: Record<AtmosPhase, { label: string; color: string }> = {
    idle: { label: '', color: '#666' },
    interpreting: { label: 'Understanding…', color: '#818cf8' },
    generating: { label: 'Writing code…', color: '#60a5fa' },
    building: { label: 'Installing…', color: '#f59e0b' },
    running: { label: 'Starting app…', color: '#34d399' },
    live: { label: 'Live', color: '#10b981' },
    error_fixing: { label: 'Fixing issue…', color: '#f87171' },
};

// ─── Store ──────────────────────────────────────────────────────────────────

interface AtmosState {
    // Phase
    phase: AtmosPhase;
    isProcessing: boolean;

    // Context
    lastIntent: string;
    statusMessage: string;
    errorContext: string | null;
    previewUrl: string | null;
    retryCount: number;

    // Actions
    transition: (next: AtmosPhase) => void;
    setStatus: (msg: string) => void;
    setError: (err: string | null) => void;
    setPreviewUrl: (url: string | null) => void;
    startIntent: (intent: string) => void;
    reset: () => void;

    // SSE connection
    abortController: AbortController | null;
    setAbortController: (ac: AbortController | null) => void;
}

export const useAtmosStore = create<AtmosState>((set, get) => ({
    // ─── Initial State ────────────────────────────────────────────────────────
    phase: 'idle',
    isProcessing: false,
    lastIntent: '',
    statusMessage: '',
    errorContext: null,
    previewUrl: null,
    retryCount: 0,
    abortController: null,

    // ─── Transition ───────────────────────────────────────────────────────────
    transition: (next: AtmosPhase) => {
        const current = get().phase;
        const valid = VALID_TRANSITIONS[current];

        if (!valid.includes(next)) {
            console.warn(`[ATMOS] Invalid transition: ${current} → ${next}`);
            return;
        }

        const isProcessing = next !== 'idle' && next !== 'live';

        set({
            phase: next,
            isProcessing,
            statusMessage: PHASE_DISPLAY[next].label,
        });

        // Emit to event bus for other panels
        EventBus.emit('ATMOS_PHASE_CHANGE', { phase: next }, 'atmos');
    },

    // ─── Status ───────────────────────────────────────────────────────────────
    setStatus: (msg: string) => {
        set({ statusMessage: msg });
        EventBus.emit('ATMOS_STATUS', { message: msg }, 'atmos');
    },

    setError: (err: string | null) => {
        set({ errorContext: err });
    },

    setPreviewUrl: (url: string | null) => {
        set({ previewUrl: url });
    },

    // ─── Intent ───────────────────────────────────────────────────────────────
    startIntent: (intent: string) => {
        const state = get();

        // Cancel any in-flight request
        if (state.abortController) {
            state.abortController.abort();
        }

        set({
            lastIntent: intent,
            errorContext: null,
            retryCount: 0,
        });

        // Transition based on current phase
        if (state.phase === 'idle' || state.phase === 'live') {
            get().transition('interpreting');
        }
    },

    reset: () => {
        const state = get();
        if (state.abortController) {
            state.abortController.abort();
        }
        set({
            phase: 'idle',
            isProcessing: false,
            lastIntent: '',
            statusMessage: '',
            errorContext: null,
            previewUrl: null,
            retryCount: 0,
            abortController: null,
        });
    },

    setAbortController: (ac: AbortController | null) => {
        set({ abortController: ac });
    },
}));

// ─── SSE Runner ─────────────────────────────────────────────────────────────

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * Send user intent to ATMOS backend and process SSE stream.
 * This is the ONLY entry point for user actions.
 * 
 * The backend does everything: interpret, generate files, install, build, run.
 * We just listen to events and update the UI.
 */
export async function runAtmosIntent(intent: string): Promise<void> {
    const store = useAtmosStore.getState();

    // Start
    store.startIntent(intent);

    const ac = new AbortController();
    store.setAbortController(ac);

    try {
        const response = await fetch(`${API_BASE}/atmos/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ intent }),
            signal: ac.signal,
        });

        if (!response.ok) {
            throw new Error(`ATMOS error: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error('No response stream');

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const raw = line.slice(6).trim();
                if (!raw || raw === '[DONE]') continue;

                try {
                    const event = JSON.parse(raw);
                    handleAtmosEvent(event);
                } catch {
                    // Skip malformed events
                }
            }
        }
    } catch (err: any) {
        if (err.name === 'AbortError') return; // User cancelled
        console.error('[ATMOS] Stream error:', err);
        store.setStatus('Connection lost. Try again.');
        store.transition('idle');
    } finally {
        store.setAbortController(null);
    }
}

// ─── Event Handler ──────────────────────────────────────────────────────────

function handleAtmosEvent(event: any) {
    const store = useAtmosStore.getState();
    const { type, ...payload } = event;

    switch (type) {
        case 'phase_change':
            store.transition(payload.phase);
            break;

        case 'status':
            store.setStatus(payload.message);
            break;

        case 'file_created':
            // Push to IDE store via event bus
            EventBus.emit('FILE_CREATED', {
                path: payload.path,
                content: payload.content,
            }, 'atmos');
            break;

        case 'file_updated':
            EventBus.emit('FILE_UPDATED', {
                path: payload.path,
                content: payload.content,
            }, 'atmos');
            break;

        case 'preview_ready':
            store.setPreviewUrl(payload.url);
            store.transition('live');
            break;

        case 'error':
            store.setError(payload.message);
            EventBus.emit('AI_ERROR', { message: payload.message }, 'atmos');
            if (payload.fixing) {
                store.transition('error_fixing');
            }
            break;

        case 'chat_message':
            EventBus.emit('AI_MESSAGE', {
                content: payload.message,
                role: 'assistant',
            }, 'atmos');
            break;

        case 'chat_token':
            // Streaming token for real-time chat typing effect
            EventBus.emit('AI_MESSAGE_TOKEN', {
                token: payload.token,
            }, 'atmos');
            break;

        case 'done':
            EventBus.emit('ATMOS_DONE', {}, 'atmos');
            // If not already live, go idle
            if (store.phase !== 'live') {
                store.transition('idle');
            }
            break;
    }
}
