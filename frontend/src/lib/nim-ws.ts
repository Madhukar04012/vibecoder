/**
 * NIM WebSocket Client — Frontend
 *
 * Connects to /ws/nim/{session_id} and translates NIM streaming events
 * into the existing EventBus events consumed by AtomsChatPanel.
 *
 * Drop-in replacement for runAtmosIntent().
 *
 * Event mapping:
 *   NIM agent_start    → EventBus AI_AGENT_ACTIVE  + PhaseBlock phase advance
 *   NIM token          → EventBus AI_THINKING_TOKEN
 *   NIM agent_complete → EventBus AI_AGENT_DONE    + progress bump
 *   NIM dag_ready      → EventBus AI_MESSAGE (execution_plan event_card)
 *   NIM dag_complete   → EventBus ATMOS_DONE       + phase = completed
 *   NIM task_error     → EventBus AI_ERROR
 */

import { EventBus } from './event-bus';
import { useAtmosStore } from './atmos-state';
import { useAgentStore } from '@/stores/agent-store';
import { useStreamStore } from '@/streaming/stream-store';
import type { Phase } from '@/streaming/phase-engine';

// ── URL helpers ───────────────────────────────────────────────────────────────

function getWsBase(): string {
  // In development with Vite dev server, use the current host (Vite proxy
  // forwards /ws/* to the backend).  Direct connection to the backend via
  // VITE_API_URL can fail due to browser security policies.
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${proto}://${window.location.host}`;
}

function generateSessionId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for older browsers
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 11)}`;
}

// ── Agent display config ──────────────────────────────────────────────────────

/** Short model display names for the chat panel */
const MODEL_SHORT_NAMES: Record<string, string> = {
  'nvidia/llama-3.3-nemotron-super-49b-v1': 'Nemotron 49B',
  'mistralai/devstral-2-123b-instruct-2512': 'Devstral 123B',
  'qwen/qwen2.5-coder-32b-instruct': 'Qwen 2.5 Coder 32B',
  'deepseek-ai/deepseek-v3.2': 'DeepSeek V3.2',
  'meta/llama-3.3-70b-instruct': 'Llama 3.3 70B',
  'qwen/qwq-32b': 'QWQ 32B',
  'moonshotai/kimi-k2-thinking': 'Kimi K2',
};

function getModelShortName(model?: string): string {
  if (!model) return '';
  return MODEL_SHORT_NAMES[model] ?? model.split('/').pop() ?? model;
}

const ROLE_DISPLAY: Record<string, { name: string; icon: string; thinking: string; model: string }> = {
  team_lead: {
    name: 'Team Leader',
    icon: 'crown',
    model: 'Nemotron 49B',
    thinking:
      "I've got the brief. Let me figure out the best approach — which agents to involve, in what order, and what each one should focus on.",
  },
  database_engineer: {
    name: 'Database Engineer',
    icon: 'database',
    model: 'Llama 3.3 70B',
    thinking:
      "Designing the data model. Tables, relationships, indexes — I'll make the schema solid before anyone writes application code.",
  },
  backend_engineer: {
    name: 'Backend Engineer',
    icon: 'server',
    model: 'Devstral 123B',
    thinking:
      "Starting on the backend now. I'll write the API endpoints, business logic, and data layer — clean, typed, and production-ready.",
  },
  frontend_engineer: {
    name: 'Frontend Engineer',
    icon: 'layout',
    model: 'Qwen 2.5 Coder 32B',
    thinking:
      "Building the frontend now. React components, TypeScript, clean UI — I'll make sure it connects properly to the backend API.",
  },
  qa_engineer: {
    name: 'QA Engineer',
    icon: 'shield-check',
    model: 'QWQ 32B',
    thinking:
      "Going through all the outputs carefully. Checking for bugs, incomplete code, and anything that doesn't meet the requirements before we ship.",
  },
};

function getRoleDisplay(role: string): { name: string; icon: string; thinking: string; model: string } {
  return (
    ROLE_DISPLAY[role] ?? {
      name: role.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      icon: 'brain',
      model: '',
      thinking: `${role} is working on this step.`,
    }
  );
}

// NIM role → stream-store Phase
const ROLE_STREAM_PHASE: Record<string, Phase> = {
  team_lead:         'planning',
  backend_engineer:  'implementation',
  frontend_engineer: 'implementation',
  database_engineer: 'architecture',
  qa_engineer:       'validation',
};

// ── Module-level state ────────────────────────────────────────────────────────

let _activeWs: WebSocket | null = null;
// Monotonically incrementing counter; gives each emitted event a unique ID
// that AtomsChatPanel can use for reliable deduplication instead of content hashing.
let _eventSeq = 0;
function nextEventId(): string {
  return `nim_evt_${++_eventSeq}`;
}

// ── Public API ─────────────────────────────────────────────────────────────────

/**
 * Run the NIM multi-agent pipeline for the given prompt.
 *
 * Connects to /ws/nim/{sessionId}, translates all NIM events into the
 * EventBus events that AtomsChatPanel already knows how to render.
 *
 * Resolves when the pipeline completes (dag_complete) or the connection closes.
 * Rejects on WebSocket connection error.
 */
export async function runNimIntent(prompt: string): Promise<void> {
  // Guard: close any existing connection before starting a new one
  if (_activeWs && _activeWs.readyState <= WebSocket.OPEN) {
    console.log('[NIM-WS] Closing previous connection before starting new one');
    _activeWs.close();
    _activeWs = null;
  }

  const store = useAtmosStore.getState();
  store.startIntent(prompt);

  const sessionId = generateSessionId();
  const wsUrl = `${getWsBase()}/ws/nim/${sessionId}`;

  console.log('[NIM-WS] Connecting to:', wsUrl);

  return new Promise<void>((resolve, reject) => {
    let runStarted = false;
    let heartbeatTimer: ReturnType<typeof setInterval> | null = null;
    let settled = false;
    let cleanedUp = false;

    const ws = new WebSocket(wsUrl);
    _activeWs = ws;
    EventBus.emit('WS_STATUS', { status: 'connecting' }, 'nim');

    // Connection timeout — if WS doesn't open within 10s, reject
    const connectTimeout = setTimeout(() => {
      if (ws.readyState !== WebSocket.OPEN) {
        console.error('[NIM-WS] Connection timeout after 10s');
        ws.close();
        if (!settled) {
          settled = true;
          reject(new Error(
            'WebSocket connection timed out after 10 seconds. Make sure the backend is running on port 8000.'
          ));
        }
      }
    }, 10_000);

    // Create AbortController that also closes the WebSocket on abort
    const ac = new AbortController();
    ac.signal.addEventListener("abort", () => {
      if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null; }
      if (_activeWs === ws) {
        ws.close();
        _activeWs = null;
      }
    }, { once: true });
    store.setAbortController(ac);

    // ── Message handler (closure over ws, runStarted) ─────────────────────
    function handleNimMessage(event: Record<string, any>) {
      const { type, agent, content } = event;

      switch (type) {

        case 'connected':
          // Server confirmed connection — nothing to render
          break;

        case 'agent_start': {
          if (!runStarted) {
            runStarted = true;

            // ① Reset PhaseBlock and start 'understanding' phase
            const ss = useStreamStore.getState();
            ss.reset();
            ss.setPhase('understanding');
            setTimeout(() => {
              useStreamStore.getState().addCheckpoint('Reading your request');
            }, 450);

            // ② "Run started" event card (timeline marker in chat)
            EventBus.emit('AI_MESSAGE', {
              _eventId: nextEventId(),
              content: 'NIM multi-agent pipeline started',
              role: 'assistant',
              agentName: 'Orchestrator',
              agentIcon: 'brain',
              messageType: 'event_card',
              eventType: 'run_started',
              eventData: {},
            }, 'nim');

            // ③ Team Leader opening message
            EventBus.emit('AI_DISCUSSION', {
              _eventId: nextEventId(),
              from: 'Team Leader',
              to: 'All',
              icon: 'crown',
              message: prompt
                ? `Got it — "${prompt}".\n\nI'm pulling the team together now. You'll see each person's work in real time as they go. Let's build this.`
                : "Got the brief. Pulling the team together now — let's build this.",
            }, 'nim');
          }

          if (agent) {
            const display = getRoleDisplay(agent as string);
            const streamPhase = ROLE_STREAM_PHASE[agent as string];
            // Get model name from WS event (sent by backend) or static config
            const modelName = getModelShortName((event as Record<string, unknown>).model as string | undefined) || display.model;

            // Advance PhaseBlock to this agent's phase
            if (streamPhase) {
              const ss = useStreamStore.getState();
              ss.completeLastPendingCheckpoint();
              ss.setPhase(streamPhase);
            }
            useStreamStore.getState().addCheckpoint(
              modelName ? `${display.name} (${modelName})` : `${display.name} is working`
            );

            // Update agent-store so AgentPanel shows live state
            useAgentStore.getState().updateAgent(agent as string, {
              state: 'working',
              currentTask: display.thinking,
              model: modelName || display.model,
            });

            // Emit AI_AGENT_ACTIVE → AtomsChatPanel starts NarrativeDrip
            EventBus.emit('AI_AGENT_ACTIVE', {
              name: display.name,
              icon: display.icon,
              thinking: display.thinking,
              model: modelName || display.model,
            }, 'nim');
          }
          break;
        }

        case 'token': {
          // Live token from the agent — feeds PhaseBlock thinking display + chat panel
          if (content) {
            EventBus.emit('AI_THINKING_TOKEN', { token: content }, 'nim');
          }
          break;
        }

        case 'agent_complete': {
          if (agent) {
            // Bump PhaseBlock progress and close the agent's thinking bubble
            useStreamStore.getState().bumpProgress(0.07, 0.92);
            EventBus.emit('AI_AGENT_DONE', {}, 'nim');

            // Update agent-store so AgentPanel shows done
            useAgentStore.getState().updateAgent(agent as string, {
              state: 'done',
              currentTask: 'Completed',
            });
          }
          break;
        }

        case 'dag_ready': {
          // TEAM_LEAD finished planning — show the execution plan in chat
          let planText = 'Execution plan ready';
          try {
            const dag = JSON.parse((content as string) || '{}');
            const tasks: any[] = dag.tasks ?? [];
            if (tasks.length > 0) {
              const roles = tasks
                .map((t: any) => (t.role as string).replace(/_/g, ' '))
                .join(' → ');
              planText = `Execution plan (${tasks.length} agents): ${roles}`;
            }
          } catch {
            // keep default text
          }

          const ss = useStreamStore.getState();
          ss.completeLastPendingCheckpoint();
          ss.setPhase('planning');
          ss.addCheckpoint('Execution plan ready');

          EventBus.emit('AI_MESSAGE', {
            _eventId: nextEventId(),
            content: planText,
            role: 'assistant',
            agentName: 'Orchestrator',
            agentIcon: 'brain',
            messageType: 'event_card',
            eventType: 'execution_plan',
            eventData: {},
          }, 'nim');
          break;
        }

        case 'task_error': {
          const agentName = agent ? getRoleDisplay(agent as string).name : 'Agent';
          EventBus.emit('AI_ERROR', {
            message: `${agentName}: ${(content as string) || 'Task failed'}`,
          }, 'nim');

          // Update agent-store so AgentPanel shows error state
          if (agent) {
            useAgentStore.getState().updateAgent(agent as string, {
              state: 'error',
              currentTask: (content as string) || 'Task failed',
            });
          }
          break;
        }

        case 'dag_complete': {
          // All agents done — mark PhaseBlock complete and fire ATMOS_DONE
          const ss = useStreamStore.getState();
          ss.setProgress(1);
          ss.setPhase('completed');
          ss.addCheckpoint('Project successfully generated');
          cleanedUp = true;
          EventBus.emit('ATMOS_DONE', {}, 'nim');

          // Keep listening for preview_ready. Close after 60s as a safety net.
          const previewTimeout = setTimeout(() => {
            if (ws.readyState === WebSocket.OPEN) {
              console.log('[NIM-WS] Closing idle WebSocket (preview timeout)');
              ws.close();
            }
          }, 60_000);

          // Clean up the timeout if the socket closes before it fires
          ws.addEventListener("close", () => clearTimeout(previewTimeout), { once: true });
          break;
        }

        case 'error': {
          EventBus.emit('AI_ERROR', {
            message: (content as string) || 'Unknown NIM error',
          }, 'nim');
          break;
        }

        case 'file_writing': {
          // Agent is starting to write a file → signal IDE to open/focus that tab
          const fwPath = (event as Record<string, unknown>).path as string | undefined;
          if (fwPath) {
            EventBus.emit('AI_FILE_WRITING', { path: fwPath }, 'nim');
            const fileName = fwPath.split('/').pop() ?? fwPath;
            useStreamStore.getState().addCheckpoint(`Writing ${fileName}`);
          }
          break;
        }

        case 'file_delta': {
          // Agent streaming a chunk of file content → typewriter into editor
          const fdPath = (event as Record<string, unknown>).path as string | undefined;
          if (fdPath && content) {
            EventBus.emit('AI_FILE_DELTA', { path: fdPath, delta: content }, 'nim');
          }
          break;
        }

        case 'file_complete': {
          // File fully generated → finalize in the IDE file tree
          const fcPath = (event as Record<string, unknown>).path as string | undefined;
          if (fcPath) {
            EventBus.emit('FILE_CREATED', { path: fcPath, content: content || '' }, 'nim');
          }
          break;
        }

        case 'agent_discussion': {
          // Team-member discussion event → renders in the discussion column
          const evtObj = event as Record<string, unknown>;
          const from = (evtObj.from as string | undefined) ?? getRoleDisplay(typeof agent === 'string' ? agent : 'team_lead').name;
          const to   = (evtObj.to   as string | undefined) ?? 'Team';
          const icon = (evtObj.icon as string | undefined) ?? 'brain';
          if (content) {
            EventBus.emit('AI_DISCUSSION', { _eventId: nextEventId(), from, to, icon, message: content }, 'nim');
          }
          break;
        }

        case 'preview_ready': {
          // Backend started a dev server → set the preview iframe URL
          if (content) {
            useAtmosStore.getState().setPreviewUrl(content as string);
            useAtmosStore.getState().transition('live');
          }
          break;
        }

        case 'pong':
          break;

        default:
          break;
      }
    }

    // ── WebSocket lifecycle ───────────────────────────────────────────────────

    ws.onopen = () => {
      clearTimeout(connectTimeout);
      console.log('[NIM-WS] Connected! Sending start message...');
      EventBus.emit('WS_STATUS', { status: 'connected' }, 'nim');
      // Reset all agents to idle before the pipeline begins
      useAgentStore.getState().reset();
      ws.send(JSON.stringify({ type: 'start', prompt }));

      // Start heartbeat — send ping every 30s to keep connection alive
      heartbeatTimer = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30_000);
    };

    ws.onmessage = (evt) => {
      try {
        const parsed = JSON.parse(evt.data as string);
        console.log('[NIM-WS] Event:', parsed.type, parsed.agent || '', parsed.content?.slice?.(0, 80) || '');
        handleNimMessage(parsed);
      } catch (e) {
        console.warn('[NIM-WS] Malformed message:', evt.data, e);
      }
    };

    ws.onerror = (err) => {
      clearTimeout(connectTimeout);
      if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null; }
      console.error('[NIM-WS] WebSocket error:', err);
      EventBus.emit('WS_STATUS', { status: 'error' }, 'nim');
      // Note: onerror fires before onclose when connection is refused
      if (!settled) {
        settled = true;
        reject(
          new Error(
            'NIM WebSocket connection failed. Is the backend running at the correct URL?'
          )
        );
      }
    };

    ws.onclose = (ev) => {
      clearTimeout(connectTimeout);
      if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null; }
      console.log('[NIM-WS] Connection closed. code=%d reason=%s', ev.code, ev.reason || '(none)');
      _activeWs = null;
      store.setAbortController(null);
      EventBus.emit('WS_STATUS', { status: 'disconnected' }, 'nim');

      // If unexpected close (not clean close code 1000), emit error + cleanup
      if (ev.code !== 1000 && ev.code !== 1005 && runStarted) {
        EventBus.emit('AI_ERROR', {
          message: `WebSocket connection lost (code: ${ev.code}). Try sending your message again.`,
        }, 'nim');
      }

      // Emit ATMOS_DONE on close to ensure UI cleanup (skip if dag_complete already fired it)
      if (runStarted && !cleanedUp) {
        cleanedUp = true;
        EventBus.emit('ATMOS_DONE', {}, 'nim');
      }

      // Reset atmos store phase so next prompt can start fresh
      useAtmosStore.getState().reset();

      if (!settled) {
        settled = true;
        resolve();
      }
    };
  });
}
