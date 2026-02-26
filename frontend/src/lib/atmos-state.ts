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
import { useStreamStore, toRosterId } from '@/streaming/stream-store';
import type { Phase } from '@/streaming/phase-engine';

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
    interpreting: ['interpreting', 'generating', 'building', 'error_fixing', 'idle'],  // multiple agents can stay in interpreting
    generating: ['generating', 'building', 'running', 'live', 'error_fixing', 'idle'],  // live/running: skip build for static projects
    building: ['building', 'running', 'live', 'error_fixing', 'idle'],               // live: skip dev server for static builds
    running: ['live', 'error_fixing', 'idle'],
    live: ['interpreting', 'idle'],   // user sends new intent
    error_fixing: ['building', 'running', 'generating', 'live', 'idle'],  // retry or give up
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

const API_BASE = import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? '' : 'http://127.0.0.1:8000');

/**
 * Send user intent to the multi-agent backend and process SSE stream.
 * This is the ONLY entry point for user actions.
 * 
 * Uses the Atoms Engine which runs a full multi-agent SDLC pipeline:
 * TeamLead → PM → Architect → Engineer → QA → DevOps
 * with inter-agent discussions visible in the chat.
 */
export async function runAtmosIntent(intent: string): Promise<void> {
    const store = useAtmosStore.getState();

    // Start
    store.startIntent(intent);

    const ac = new AbortController();
    store.setAbortController(ac);

    try {
        const response = await fetch(`${API_BASE}/api/atoms/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: intent, files: {}, mode: 'standard' }),
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
        store.setError(err?.message ?? 'Connection lost');
        store.setStatus('Connection lost. Try again.');
        store.transition('idle');
        throw err;
    } finally {
        store.setAbortController(null);
    }
}

// ─── Event Handler ──────────────────────────────────────────────────────────

// Scoped state per-intent to prevent race conditions when intents overlap.
// Reset in handleAtmosEvent on 'run_start' or by the store's startIntent().
const _intentState = {
    activeAgentId: null as string | null,
    lastCpId: null as string | null,
    fileCount: 0,
    reset() {
        this.activeAgentId = null;
        this.lastCpId = null;
        this.fileCount = 0;
    },
};

// Map atoms_engine phases to atmos phases based on agent progress
function agentToPhase(agent: string): AtmosPhase | null {
    switch (agent) {
        // Unified pipeline agent ids
        case 'planner': return 'interpreting';
        case 'db_schema': return 'interpreting';
        case 'auth': return 'interpreting';
        case 'coder': return 'generating';
        case 'code_reviewer': return 'generating';
        case 'tester': return 'generating';
        case 'deployer': return 'building';

        // Legacy atoms ids
        case 'team_lead': return 'interpreting';
        case 'pm': return 'interpreting';
        case 'architect': return 'interpreting';
        case 'engineer': return 'generating';
        case 'qa': return 'generating';
        case 'devops': return 'building';
        default: return null;
    }
}

const AGENT_NARRATIVE: Record<string, { name: string; icon: string; thinking: string; done: string }> = {
    planner: {
        name: 'Planner',
        icon: 'map',
        thinking: "Alright, let me read through the requirements carefully and figure out exactly what we're building here. I'll map out the full execution sequence so the team knows what to tackle and in what order.",
        done: 'Planning complete. Execution sequence is locked in — handing off to the team now.',
    },
    db_schema: {
        name: 'Architect',
        icon: 'layers',
        thinking: "Looking at the requirements now. Let me design the data model — tables, relationships, indexes — and figure out the right technical structure before anyone writes a line of code.",
        done: 'Data model and schema decisions are done. Architecture is solid.',
    },
    auth: {
        name: 'Engineer',
        icon: 'code',
        thinking: "Wiring up authentication now. JWT tokens, hashed passwords, route protection — I'll make sure access control is airtight before we add any features on top.",
        done: 'Auth layer is live. Login, registration, and protected routes are implemented.',
    },
    coder: {
        name: 'Engineer',
        icon: 'code',
        thinking: "Generating the full project now. I'm laying out the folder structure, writing each file based on the architecture, and making sure everything connects cleanly end to end.",
        done: 'Code generation complete. All files are written and the project structure is ready.',
    },
    code_reviewer: {
        name: 'QA Engineer',
        icon: 'shield',
        thinking: "Reading through the generated code carefully. Checking for bugs, security issues, and anything that doesn't match the spec. I'll flag anything the team needs to fix before shipping.",
        done: 'Code review done. Findings logged — the build is clean and ready for testing.',
    },
    tester: {
        name: 'QA Engineer',
        icon: 'shield',
        thinking: "Running through the test cases now. I want to make sure every critical path works, edge cases are handled, and nothing obvious is broken before we ship this.",
        done: 'All tests passed. No regressions. The build is good to go.',
    },
    deployer: {
        name: 'DevOps',
        icon: 'rocket',
        thinking: "Setting up the deployment environment now. Installing dependencies, configuring the runtime, writing the Dockerfile and compose config — making sure this runs cleanly everywhere.",
        done: 'Deployment config is ready. Docker, dependencies, and runtime are all set up.',
    },
    team_lead: {
        name: 'Team Leader',
        icon: 'crown',
        thinking: "I've got the brief. Let me figure out the best approach here — which agents to involve, in what order, and what each person should focus on. I'll keep the team coordinated throughout.",
        done: "Coordination complete. The team has everything they need — wrapping up execution.",
    },
    pm: {
        name: 'Product Manager',
        icon: 'clipboard',
        thinking: "Digging into the requirements now. I want to make sure we're building the right thing — clear user flows, well-defined features, no ambiguity before the team starts coding.",
        done: 'Requirements are locked in. The team has a clear, unambiguous spec to work from.',
    },
    architect: {
        name: 'Architect',
        icon: 'layers',
        thinking: "Thinking through the system design. I need to define how the pieces fit together — frontend, backend, database, APIs, and any external services — before anyone starts building.",
        done: 'Architecture is defined. Component boundaries are clear and the design is solid.',
    },
    engineer: {
        name: 'Engineer',
        icon: 'code',
        thinking: "Let me get into the code. I'll implement this step by step — following the architecture, keeping the code clean, and making sure everything integrates properly with what's already been built.",
        done: 'Implementation done. This piece is built, tested, and ready to hand off.',
    },
    qa: {
        name: 'QA Engineer',
        icon: 'shield',
        thinking: "Going through the output carefully now. I'm checking behavior, looking for edge cases, and making sure the quality bar is high enough to ship.",
        done: 'QA complete. Everything checks out — no critical issues found.',
    },
    devops: {
        name: 'DevOps',
        icon: 'rocket',
        thinking: "Handling the infrastructure side now. Getting the build pipeline, environment config, and deployment setup sorted — making sure this actually runs in production, not just locally.",
        done: 'Infrastructure is ready. Build, deploy, and runtime configs are all in place.',
    },
};

// ─── Agent → Phase mapping ────────────────────────────────────────────────────

function agentToStreamPhase(agentId: string): Phase | null {
    switch (agentId) {
        case 'team_lead':
        case 'planner':
        case 'pm':
            return 'planning';
        case 'architect':
        case 'db_schema':
            return 'architecture';
        case 'engineer':
        case 'coder':
        case 'auth':
            return 'implementation';
        case 'qa':
        case 'tester':
        case 'code_reviewer':
        case 'deployer':
        case 'devops':
            return 'validation';
        default:
            return null;
    }
}

// lastCpId and fileCount live on _intentState (line 246) to prevent race conditions

function resolveAgentNarrative(agentId: string, payloadName?: string, payloadIcon?: string) {
    const base = AGENT_NARRATIVE[agentId];
    const fallbackName = agentId.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    return {
        name: payloadName || base?.name || fallbackName,
        icon: payloadIcon || base?.icon || 'brain',
        thinking: base?.thinking || `${payloadName || fallbackName} is working on this step.`,
        done: base?.done || `${payloadName || fallbackName} completed this step.`,
    };
}

function handleAtmosEvent(event: any) {
    const store = useAtmosStore.getState();
    const { type, ...payload } = event;

    switch (type) {
        // ── Phase transitions ────────────────────────────────────
        case 'phase_change':
            store.transition(payload.phase);
            break;

        case 'status':
            store.setStatus(payload.message);
            break;

        // ── Unified pipeline metadata events ─────────────────────
        case 'run_started': {
            // ── Phase: understanding ──────────────────────────────────────
            _intentState.fileCount = 0;
            _intentState.lastCpId = null;
            const ss0 = useStreamStore.getState();
            // Hard-reset phase state (previous run may have been in 'completed')
            ss0.reset();
            ss0.setPhase('understanding');
            // setPhase has a 400ms delay, so add checkpoint immediately after
            setTimeout(() => {
                _intentState.lastCpId = useStreamStore.getState().addCheckpoint('Reading your request');
            }, 450);

            const mode = typeof payload.mode === 'string' ? payload.mode : 'full';
            const tier = typeof payload.token_tier === 'string' ? payload.token_tier : 'free';
            const intent = (store.lastIntent || '').trim();
            EventBus.emit('AI_MESSAGE', {
                content: `Run started (${mode} mode, ${tier} tier)`,
                role: 'assistant',
                agentName: 'Orchestrator',
                agentIcon: 'brain',
                messageType: 'event_card',
                eventType: 'run_started',
                eventData: payload,
            }, 'atoms');
            EventBus.emit('AI_DISCUSSION', {
                from: 'Team Leader',
                to: 'All',
                icon: 'crown',
                message: intent
                    ? `Got it — "${intent}".\n\nI'm pulling the team together now. You'll see each person's work in real time as they go. Let's build this.`
                    : "Got the brief. Pulling the team together now — you'll see each person's work as they go. Let's build this.",
            }, 'atoms');

            const chatModel = typeof payload.chat_model === 'string' ? payload.chat_model : '';
            const coderModel = typeof payload.coder_model === 'string' ? payload.coder_model : '';
            if (chatModel || coderModel) {
                const modelContent =
                    chatModel && coderModel && chatModel !== coderModel
                        ? `Models: Chat ${chatModel} | Code ${coderModel}`
                        : `Model: ${coderModel || chatModel}`;
                EventBus.emit('AI_MESSAGE', {
                    content: modelContent,
                    role: 'assistant',
                    agentName: 'Orchestrator',
                    agentIcon: 'brain',
                    messageType: 'event_card',
                    eventType: 'model_configured',
                    eventData: { chatModel, coderModel },
                }, 'atoms');
            }
            break;
        }

        case 'budget_configured': {
            const tier = typeof payload.tier === 'string'
                ? payload.tier
                : (typeof payload.token_tier === 'string' ? payload.token_tier : 'free');

            const cap = payload.daily_cap_usd;
            const spent = Number(payload.spent_usd);
            const remaining = Number(payload.remaining_usd);

            const fmt = (n: number) => Number.isFinite(n) ? `$${n.toFixed(2)}` : null;
            const capNum = typeof cap === 'number' ? cap : Number(cap);
            const capText = cap == null ? 'No daily cap' : (fmt(capNum) ?? 'No daily cap');

            let content = `Budget (${tier}): ${capText}`;
            const remainingText = fmt(remaining);
            const spentText = fmt(spent);
            if (remainingText) content += ` | Remaining ${remainingText}`;
            if (spentText) content += ` | Spent ${spentText}`;

            EventBus.emit('AI_MESSAGE', {
                content,
                role: 'assistant',
                agentName: 'Orchestrator',
                agentIcon: 'brain',
                messageType: 'event_card',
                eventType: 'budget_configured',
                eventData: payload,
            }, 'atoms');
            break;
        }

        case 'execution_plan': {
            // ── Phase: planning ───────────────────────────────────────────
            const ss1 = useStreamStore.getState();
            ss1.completeLastPendingCheckpoint();
            ss1.setPhase('planning');

            const order = Array.isArray(payload.execution_order)
                ? payload.execution_order.map((s: any) => String(s).replace(/_/g, ' '))
                : [];

            if (order.length > 0) {
                _intentState.lastCpId = ss1.addCheckpoint(`Sequence: ${order.slice(0, 4).join(' → ')}${order.length > 4 ? '…' : ''}`);
            } else {
                _intentState.lastCpId = ss1.addCheckpoint('Execution plan ready');
            }

            const content = order.length > 0
                ? `Execution plan: ${order.join(' -> ')}`
                : 'Execution plan ready';

            EventBus.emit('AI_MESSAGE', {
                content,
                role: 'assistant',
                agentName: 'Orchestrator',
                agentIcon: 'brain',
                messageType: 'event_card',
                eventType: 'execution_plan',
                eventData: payload,
            }, 'atoms');
            EventBus.emit('AI_DISCUSSION', {
                from: 'Team Leader',
                to: 'All',
                icon: 'crown',
                message: order.length > 0
                    ? `Here's the plan: ${order.join(' → ')}. Each person will take their turn — I'll keep things moving.`
                    : "Execution plan is locked in. Let's get started.",
            }, 'atoms');
            break;
        }

        // ── Agent lifecycle (from atoms_engine) ──────────────────
        case 'agent_start': {
            const narrative = resolveAgentNarrative(
                String(payload.agent || ''),
                typeof payload.name === 'string' ? payload.name : undefined,
                typeof payload.icon === 'string' ? payload.icon : undefined,
            );
            const agentPhase = agentToPhase(payload.agent);
            if (agentPhase) {
                const current = store.phase;
                const valid = ['idle', 'interpreting', 'generating', 'building', 'running', 'error_fixing', 'live'];
                if (valid.includes(current)) {
                    try { store.transition(agentPhase); } catch { /* skip invalid transition */ }
                }
            }

            // ── Phase engine: advance stream phase ────────────────
            const streamPhaseForAgent = agentToStreamPhase(String(payload.agent || ''));
            const ssAgent = useStreamStore.getState();
            if (streamPhaseForAgent) {
                ssAgent.completeLastPendingCheckpoint();
                ssAgent.setPhase(streamPhaseForAgent);
            }
            _intentState.lastCpId = ssAgent.addCheckpoint(`${narrative.name} is working`);

            // Track active agent so message tokens get routed to thinking display
            _intentState.activeAgentId = String(payload.agent || '');

            // ── Drive agent presence bar ─────────────────────────
            const rosterIdStart = toRosterId(String(payload.agent || ''));
            if (rosterIdStart) {
                ssAgent.setAgentStatus(rosterIdStart, 'working');
            }

            EventBus.emit('AI_AGENT_START', {
                agent: payload.agent,
                name: narrative.name,
                icon: narrative.icon,
                description: payload.description,
            }, 'atoms');

            // Emit the thinking block event — adds a Claude-style thinking card to chat
            EventBus.emit('AI_AGENT_ACTIVE', {
                name: narrative.name,
                icon: narrative.icon,
                thinking: narrative.thinking,
            }, 'atoms');

            // Route to terminal log
            EventBus.emit('TERMINAL_OUTPUT', {
                text: `${narrative.name}_started`,
                type: 'stdout',
            }, 'atoms');
            break;
        }

        case 'agent_end': {
            const narrative = resolveAgentNarrative(
                String(payload.agent || ''),
                typeof payload.name === 'string' ? payload.name : undefined,
                typeof payload.icon === 'string' ? payload.icon : undefined,
            );

            // Clear active agent tracking
            _intentState.activeAgentId = null;

            // ── Phase engine: mark checkpoint done + bump progress ─
            const ssEnd = useStreamStore.getState();
            if (_intentState.lastCpId) {
                ssEnd.completeCheckpoint(_intentState.lastCpId);
                _intentState.lastCpId = null;
            } else {
                ssEnd.completeLastPendingCheckpoint();
            }
            ssEnd.bumpProgress(0.06, 0.92);

            // ── Mark agent done in presence bar ──────────────────
            const rosterIdEnd = toRosterId(String(payload.agent || ''));
            if (rosterIdEnd) {
                ssEnd.setAgentStatus(rosterIdEnd, 'done');
            }

            // ── Add narrative checkmark (dev/debug) ───────────────
            ssEnd.addNarrativeItem(narrative.done);

            EventBus.emit('AI_AGENT_END', {
                agent: payload.agent,
                result: payload.result,
            }, 'atoms');

            // Close the thinking block
            EventBus.emit('AI_AGENT_DONE', {
                name: narrative.name,
                icon: narrative.icon,
                result: payload.result,
            }, 'atoms');

            // Show the agent's result as a regular message if there's content
            if (payload.result) {
                EventBus.emit('AI_MESSAGE', {
                    content: payload.result,
                    role: 'assistant',
                    agentName: narrative.name,
                    agentIcon: narrative.icon,
                    messageType: 'agent_result',
                }, 'atoms');
            }
            // Route to terminal log
            EventBus.emit('TERMINAL_OUTPUT', {
                text: `${narrative.name}_completed`,
                type: 'stdout',
            }, 'atoms');
            break;
        }

        // ── Agent-to-agent discussions ───────────────────────────
        case 'discussion':
            EventBus.emit('AI_DISCUSSION', {
                from: payload.from,
                to: payload.to,
                icon: payload.icon,
                message: payload.message,
            }, 'atoms');
            break;

        // ── File events (atoms_engine uses file_start/delta/end) ─
        case 'file_start':
            // Signal the editor panel to open the file and enable live-writing mode.
            // We intentionally do NOT add a per-file chat message here — with many files
            // that would flood the chat with dozens of "Writing X..." status bubbles.
            EventBus.emit('AI_FILE_WRITING', {
                path: payload.path,
            }, 'atoms');
            // Emit a single status token so the streaming placeholder updates
            if (payload.path) {
                EventBus.emit('AI_MESSAGE_TOKEN', {
                    token: `Writing ${payload.path}…\n`,
                }, 'atoms');
            }
            break;

        case 'file_delta':
            EventBus.emit('AI_FILE_DELTA', {
                path: payload.path,
                delta: payload.delta,
            }, 'atoms');
            break;

        case 'file_end':
            // atoms_engine file_end doesn't include content — flush live writer
            EventBus.emit('FILE_CREATED', {
                path: payload.path,
                content: '', // content was streamed via deltas
            }, 'atoms');
            // Bump phase progress as files complete
            _intentState.fileCount++;
            useStreamStore.getState().bumpProgress(0.02, 0.92);
            // No per-file chat message — the editor already shows the live content
            break;

        // ── File events (atmos.py style) ─────────────────────────
        case 'file_created':
            EventBus.emit('FILE_CREATED', {
                path: payload.path,
                content: payload.content,
            }, 'atmos');
            _intentState.fileCount++;
            useStreamStore.getState().bumpProgress(0.02, 0.92);
            break;

        case 'file_token':
            EventBus.emit('AI_FILE_DELTA', {
                path: payload.path,
                delta: payload.token,
            }, 'atmos');
            break;

        case 'file_writing':
            EventBus.emit('AI_FILE_WRITING', {
                path: payload.path,
            }, 'atmos');
            break;

        case 'file_updated':
            EventBus.emit('FILE_UPDATED', {
                path: payload.path,
                content: payload.content,
            }, 'atmos');
            break;

        // ── Preview ──────────────────────────────────────────────
        case 'preview_ready':
            store.setPreviewUrl(payload.url);
            store.transition('live');
            break;

        // ── Errors ───────────────────────────────────────────────
        case 'error':
            store.setError(payload.message);
            EventBus.emit('AI_ERROR', { message: payload.message }, 'atoms');
            EventBus.emit('TERMINAL_OUTPUT', {
                text: `ERROR: ${payload.message}`,
                type: 'stderr',
            }, 'atoms');
            if (payload.fixing) {
                store.transition('error_fixing');
            }
            break;

        // ── Chat messages (both engines) ─────────────────────────
        case 'chat_message':
            EventBus.emit('AI_MESSAGE', {
                content: payload.message,
                role: 'assistant',
            }, 'atoms');
            break;

        case 'message':
            EventBus.emit('AI_MESSAGE', {
                content: payload.content,
                role: 'assistant',
            }, 'atoms');
            // Route build/deploy messages to terminal panel (backend may send type: 'stderr' | 'stdout')
            if (payload.content) {
                EventBus.emit('TERMINAL_OUTPUT', {
                    text: payload.content,
                    type: (payload.type === 'stderr' ? 'stderr' : 'stdout') as 'stdout' | 'stderr',
                }, 'atoms');
            }
            break;

        case 'chat_token':
            if (_intentState.activeAgentId) {
                // Agent is working — stream into the thinking block
                EventBus.emit('AI_THINKING_TOKEN', { token: payload.token }, 'atoms');
            } else {
                EventBus.emit('AI_MESSAGE_TOKEN', { token: payload.token }, 'atoms');
            }
            break;

        case 'message_token':
            if (_intentState.activeAgentId) {
                // Agent is working — stream into the thinking block
                EventBus.emit('AI_THINKING_TOKEN', { token: payload.token }, 'atoms');
            } else {
                EventBus.emit('AI_MESSAGE_TOKEN', { token: payload.token }, 'atoms');
            }
            break;

        // ── Thinking tokens (ATMOS real-time reasoning) ─────────
        case 'thinking_token':
            // Always route to thinking block — these come during interpret phase
            EventBus.emit('AI_THINKING_TOKEN', { token: payload.token }, 'atoms');
            break;

        // ── Stream lifecycle events ──────────────────────────────
        case 'stream_start':
            EventBus.emit('AI_AGENT_ACTIVE', {
                name: payload.channel === 'thinking' ? 'Interpreter' : 'Engineer',
                icon: payload.channel === 'thinking' ? 'brain' : 'code',
                thinking: payload.channel === 'thinking'
                    ? 'Analyzing your request and planning the approach…'
                    : 'Generating code…',
            }, 'atmos');
            useStreamStore.getState().setAgentActive(true);
            break;

        case 'stream_end':
            // Channel stream completed — frontend can flush buffers
            if (payload.channel === 'thinking') {
                EventBus.emit('AI_AGENT_DONE', {
                    name: 'Interpreter',
                    icon: 'brain',
                    result: 'Analysis complete',
                }, 'atmos');
            }
            break;

        // ── Blackboard updates → Event cards ─────────────────────
        case 'blackboard_update': {
            const field = payload.field;

            // Skip noisy internal state transitions
            if (field === 'state') break;

            const eventLabels: Record<string, string> = {
                project_type: 'project_analyzed',
                detected_stack: 'stack_detected',
                prd: 'execution_plan',
                architecture: 'architecture_designed',
                file_plan: 'file_plan_ready',
                qa_result: 'qa_complete',
            };
            const label = eventLabels[field] || field;

            // Build readable content from the structured data
            let content = label;
            const val = payload.value;
            if (field === 'prd' && val) {
                const title = val.title || val.name || '';
                const features = val.features || [];
                const featureList = features.slice(0, 5).map((f: any) => typeof f === 'string' ? f : f.name || f.title || '').filter(Boolean).join(', ');
                content = title ? `${title}` : 'Execution plan ready';
                if (featureList) content += `\nFeatures: ${featureList}`;
            } else if (field === 'architecture' && val) {
                const dirStructure = val.directory_structure;
                const fileCount = dirStructure ? Object.keys(dirStructure).length : (val.files ? val.files.length : 0);
                content = `Architecture designed — ${fileCount} components planned`;
            } else if (field === 'detected_stack' && val) {
                const framework = val.framework || val.name || '';
                const lang = val.language || '';
                content = `Stack detected: ${[framework, lang].filter(Boolean).join(' / ') || 'auto-detected'}`;
            } else if (field === 'qa_result' && val) {
                const score = val.overall_score || val.score;
                const verdict = val.verdict || '';
                content = score ? `QA Score: ${score}/100${verdict ? ` — ${verdict}` : ''}` : 'QA review complete';
            } else if (field === 'project_type' && val) {
                content = `Project type: ${typeof val === 'string' ? val : JSON.stringify(val)}`;
            }

            // ── Add as phase checkpoint + narrative checkmark ────
            const narrativeText = (() => {
                if (field === 'prd') return 'Execution plan finalized';
                if (field === 'detected_stack') return content;
                if (field === 'architecture') return content;
                if (field === 'qa_result') return content;
                if (field === 'project_type') return content;
                return null;
            })();
            if (narrativeText) {
                const ssBb = useStreamStore.getState();
                ssBb.addNarrativeItem(narrativeText);
                // Also surface as a checkpoint in the PhaseBlock
                ssBb.addCheckpoint(narrativeText);
            }

            EventBus.emit('AI_MESSAGE', {
                content,
                role: 'assistant',
                agentName: 'Orchestrator',
                agentIcon: 'brain',
                messageType: 'event_card',
                eventType: label,
                eventData: val,
            }, 'atoms');
            // Route to terminal
            EventBus.emit('TERMINAL_OUTPUT', {
                text: label,
                type: 'stdout',
            }, 'atoms');
            break;
        }

        // ── Race mode events ─────────────────────────────────────
        case 'race_start':
        case 'race_progress':
        case 'race_result':
            // Could be visualized later
            break;

        // ── Done ─────────────────────────────────────────────────
        case 'done':
            _intentState.activeAgentId = null;
            _intentState.lastCpId = null;

            // ── Phase engine: completed ───────────────────────────
            {
                const ssDone = useStreamStore.getState();
                ssDone.completeLastPendingCheckpoint();
                // Immediate progress to 1 then phase to completed (setPhase has 400ms delay)
                ssDone.setProgress(1);
                ssDone.setPhase('completed');
                ssDone.addCheckpoint('Project successfully generated');
            }

            EventBus.emit('ATMOS_DONE', {}, 'atoms');
            if (store.phase !== 'live') {
                store.transition('idle');
            }
            // Do NOT auto-reset — CompletionCard stays visible. User can reset by starting new run.
            break;
    }
}
