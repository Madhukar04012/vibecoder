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
        thinking: 'I am analyzing your request and turning it into a clear execution plan.',
        done: 'Planning is complete. The execution order is ready for the team.',
    },
    db_schema: {
        name: 'Architect',
        icon: 'layers',
        thinking: 'I am designing the data model and technical structure for this build.',
        done: 'Architecture and schema decisions are complete.',
    },
    auth: {
        name: 'Engineer',
        icon: 'code',
        thinking: 'I am wiring authentication and core access controls.',
        done: 'Authentication layer is implemented and handed off.',
    },
    coder: {
        name: 'Engineer',
        icon: 'code',
        thinking: 'I am generating project files and implementing the requested features.',
        done: 'Core code generation is complete.',
    },
    code_reviewer: {
        name: 'QA Engineer',
        icon: 'shield',
        thinking: 'I am reviewing generated code quality, safety, and consistency.',
        done: 'Code review is complete with findings and recommendations.',
    },
    tester: {
        name: 'QA Engineer',
        icon: 'shield',
        thinking: 'I am validating behavior and checking for regressions.',
        done: 'QA checks are complete.',
    },
    deployer: {
        name: 'DevOps',
        icon: 'rocket',
        thinking: 'I am preparing dependencies and runtime deployment.',
        done: 'Deployment step is complete.',
    },
    team_lead: {
        name: 'Team Leader',
        icon: 'crown',
        thinking: 'I am coordinating agents and managing execution flow.',
        done: 'Coordination step is complete.',
    },
    pm: {
        name: 'Product Manager',
        icon: 'clipboard',
        thinking: 'I am refining requirements and scope for execution.',
        done: 'Requirements are finalized.',
    },
    architect: {
        name: 'Architect',
        icon: 'layers',
        thinking: 'I am mapping architecture and component boundaries.',
        done: 'Architecture design is complete.',
    },
    engineer: {
        name: 'Engineer',
        icon: 'code',
        thinking: 'I am implementing the code now.',
        done: 'Implementation for this step is complete.',
    },
    qa: {
        name: 'QA Engineer',
        icon: 'shield',
        thinking: 'I am testing the output for quality and defects.',
        done: 'Testing step is complete.',
    },
    devops: {
        name: 'DevOps',
        icon: 'rocket',
        thinking: 'I am handling build and deployment setup.',
        done: 'Build/deploy step is complete.',
    },
};

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
            const mode = typeof payload.mode === 'string' ? payload.mode : 'full';
            const tier = typeof payload.token_tier === 'string' ? payload.token_tier : 'free';
            const intent = (store.lastIntent || '').trim();
            EventBus.emit('AI_MESSAGE', {
                content: `Run started (${mode} mode, ${tier} tier)`,
                role: 'assistant',
                agentName: 'AI Team',
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
                    ? `I received your requirement: "${intent}".\n\nI am assigning the team now and will post live thinking + execution updates as each agent works.`
                    : 'I received your requirement. I am assigning the team now and will post live thinking + execution updates as each agent works.',
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
                    agentName: 'AI Team',
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
                agentName: 'AI Team',
                agentIcon: 'brain',
                messageType: 'event_card',
                eventType: 'budget_configured',
                eventData: payload,
            }, 'atoms');
            break;
        }

        case 'execution_plan': {
            const order = Array.isArray(payload.execution_order)
                ? payload.execution_order.map((s: any) => String(s).replace(/_/g, ' '))
                : [];
            const content = order.length > 0
                ? `Execution plan: ${order.join(' -> ')}`
                : 'Execution plan ready';

            EventBus.emit('AI_MESSAGE', {
                content,
                role: 'assistant',
                agentName: 'AI Team',
                agentIcon: 'brain',
                messageType: 'event_card',
                eventType: 'execution_plan',
                eventData: payload,
            }, 'atoms');
            EventBus.emit('AI_DISCUSSION', {
                from: 'Team Leader',
                to: 'All',
                icon: 'crown',
                message: content,
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
            EventBus.emit('AI_AGENT_START', {
                agent: payload.agent,
                name: narrative.name,
                icon: narrative.icon,
                description: payload.description,
            }, 'atoms');

            EventBus.emit('AI_DISCUSSION', {
                from: narrative.name,
                to: 'Team Leader',
                icon: narrative.icon,
                message: narrative.thinking,
            }, 'atoms');

            // Show agent status in chat as event card
            EventBus.emit('AI_MESSAGE', {
                content: payload.description || `${narrative.name} is working...`,
                role: 'assistant',
                agentName: narrative.name,
                agentIcon: narrative.icon,
                messageType: 'agent_status',
                eventType: `${payload.agent}_started`,
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
            EventBus.emit('AI_AGENT_END', {
                agent: payload.agent,
                result: payload.result,
            }, 'atoms');
            EventBus.emit('AI_DISCUSSION', {
                from: narrative.name,
                to: 'Team Leader',
                icon: narrative.icon,
                message: typeof payload.result === 'string' && payload.result.trim()
                    ? `${narrative.done}\n${payload.result}`
                    : narrative.done,
            }, 'atoms');
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
            EventBus.emit('AI_FILE_WRITING', {
                path: payload.path,
            }, 'atoms');
            if (payload.path) {
                EventBus.emit('AI_MESSAGE', {
                    content: `Writing ${payload.path}...`,
                    role: 'assistant',
                    agentName: 'Engineer',
                    agentIcon: 'code',
                    messageType: 'agent_status',
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
            // atoms_engine file_end doesn't include content, flush live writer
            EventBus.emit('FILE_CREATED', {
                path: payload.path,
                content: '', // content was streamed via deltas
            }, 'atoms');
            if (payload.path) {
                EventBus.emit('AI_MESSAGE', {
                    content: `Finished ${payload.path}`,
                    role: 'assistant',
                    agentName: 'Engineer',
                    agentIcon: 'code',
                    messageType: 'agent_result',
                }, 'atoms');
            }
            break;

        // ── File events (atmos.py style) ─────────────────────────
        case 'file_created':
            EventBus.emit('FILE_CREATED', {
                path: payload.path,
                content: payload.content,
            }, 'atmos');
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
            EventBus.emit('AI_MESSAGE_TOKEN', {
                token: payload.token,
            }, 'atoms');
            break;

        case 'message_token':
            EventBus.emit('AI_MESSAGE_TOKEN', {
                token: payload.token,
            }, 'atoms');
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

            EventBus.emit('AI_MESSAGE', {
                content,
                role: 'assistant',
                agentName: 'AI Team',
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
            EventBus.emit('ATMOS_DONE', {}, 'atoms');
            if (store.phase !== 'live') {
                store.transition('idle');
            }
            break;
    }
}
