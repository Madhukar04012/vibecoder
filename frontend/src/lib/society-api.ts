/**
 * Society API — document-driven workflow, documents, templates, WebSocket
 */
import { apiFetch } from "./api";

export interface CreatePRDResponse {
  doc_id: string;
  title: string;
  markdown: string;
  project_name: string;
  user_story_count: number;
}

export interface WorkflowResponse {
  run_id: string;
  doc_ids: string[];
  project_name?: string;
}

export interface DocumentResponse {
  doc_id: string;
  title: string;
  doc_type: string;
  created_by: string;
  status: string;
  content_markdown: string;
  version: number;
}

export interface AgentStatusResponse {
  run_id: string;
  status: string;
  doc_ids: string[];
}

export interface RunMetrics {
  total_executions: number;
  executions_by_agent: Record<string, number>;
  avg_duration_by_agent: Record<string, number>;
  success_rate_by_agent: Record<string, number>;
  cost_by_agent: Record<string, number>;
  total_cost: number;
}

// ── REST endpoints ─────────────────────────────────────────────────────────

export async function createPRD(user_idea: string, run_id?: string): Promise<CreatePRDResponse> {
  return apiFetch<CreatePRDResponse>("/api/society/prd", {
    method: "POST",
    body: JSON.stringify({ user_idea, run_id: run_id ?? "default_run" }),
  });
}

export async function runWorkflow(user_idea: string, run_id?: string): Promise<WorkflowResponse> {
  return apiFetch<WorkflowResponse>("/api/society/workflow", {
    method: "POST",
    body: JSON.stringify({ user_idea, run_id }),
  });
}

export async function getAgentStatus(run_id: string): Promise<AgentStatusResponse> {
  return apiFetch<AgentStatusResponse>(`/api/society/agents/status/${run_id}`);
}

export async function listDocuments(run_id: string): Promise<DocumentResponse[]> {
  return apiFetch<DocumentResponse[]>(`/api/society/documents/${run_id}`);
}

export async function getDocument(doc_id: string): Promise<DocumentResponse> {
  return apiFetch<DocumentResponse>(`/api/society/documents/doc/${doc_id}`);
}

export async function listTemplates(): Promise<string[]> {
  return apiFetch<string[]>("/api/society/templates");
}

export async function approveDocument(doc_id: string, approved_by?: string): Promise<{ status: string }> {
  return apiFetch<{ status: string }>(`/api/society/documents/${doc_id}/approve?approved_by=${approved_by ?? "user"}`, {
    method: "POST",
  });
}

export async function documentFeedback(doc_id: string, feedback: string): Promise<{ status: string }> {
  return apiFetch<{ status: string }>(`/api/society/documents/${doc_id}/feedback`, {
    method: "POST",
    body: JSON.stringify({ feedback }),
  });
}

export async function getRunMetrics(run_id: string): Promise<RunMetrics> {
  return apiFetch<RunMetrics>(`/api/society/runs/${run_id}/metrics`);
}

export async function getRunTraces(run_id: string): Promise<unknown[]> {
  return apiFetch<unknown[]>(`/api/society/runs/${run_id}/traces`);
}

// ── WebSocket client ───────────────────────────────────────────────────────

export type WsEventType =
  | "event"
  | "status"
  | "ping"
  | "thinking"    // agent reasoning line while LLM is working
  | "doc_start"   // agent finished, about to type document
  | "doc_delta"   // character chunk being typed
  | "doc_end";    // typing complete for this document

export interface WsMessage {
  type: WsEventType;
  // present on "event" messages
  agent?: string;
  event?: string;
  payload?: Record<string, unknown>;
  // present on "status" messages
  data?: Record<string, unknown>;
  // present on "thinking" messages
  line?: string;
  // present on "doc_start" / "doc_delta" / "doc_end" messages
  doc_id?: string;
  title?: string;
  delta?: string;
}

export type WsMessageHandler = (msg: WsMessage) => void;

/**
 * Subscribe to real-time workflow events for a run_id.
 * Returns an unsubscribe function — call it to close the WebSocket.
 *
 * Usage:
 *   const unsub = subscribeToRun(runId, (msg) => { ... });
 *   // later:
 *   unsub();
 */
export function subscribeToRun(
  run_id: string,
  onMessage: WsMessageHandler,
  onClose?: () => void,
): () => void {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.hostname;
  // Use port 8000 in dev, same port in production
  const port = import.meta.env.DEV ? ":8000" : "";
  const url = `${protocol}//${host}${port}/api/society/ws/updates/${run_id}`;

  let ws: WebSocket | null = new WebSocket(url);
  let pingInterval: ReturnType<typeof setInterval> | null = null;
  let closed = false;

  ws.onopen = () => {
    // Send periodic client pings every 25 seconds to keep connection alive
    pingInterval = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 25_000);
  };

  ws.onmessage = (evt) => {
    try {
      const msg = JSON.parse(evt.data) as WsMessage;
      if (msg.type !== "ping") {
        onMessage(msg);
      }
    } catch {
      // ignore malformed messages
    }
  };

  ws.onclose = () => {
    if (pingInterval) clearInterval(pingInterval);
    if (!closed) onClose?.();
  };

  ws.onerror = () => {
    ws?.close();
  };

  return () => {
    closed = true;
    if (pingInterval) clearInterval(pingInterval);
    ws?.close();
    ws = null;
  };
}
