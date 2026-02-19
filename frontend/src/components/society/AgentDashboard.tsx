/**
 * Live Agent Dashboard — real-time agent status with thinking line display.
 * Shows per-agent thinking lines while the LLM is working.
 */
import React, { useEffect, useRef, useState } from "react";
import { subscribeToRun, type WsMessage } from "@/lib/society-api";

const AGENT_ORDER = [
  "product_manager",
  "architect",
  "api_designer",
  "project_manager",
  "engineer",
  "qa_engineer",
  "devops",
  "tech_writer",
] as const;

const ROLE_LABELS: Record<string, string> = {
  product_manager: "Product Manager",
  architect: "Architect",
  api_designer: "API Designer",
  project_manager: "Project Manager",
  engineer: "Engineer",
  qa_engineer: "QA Engineer",
  devops: "DevOps",
  tech_writer: "Tech Writer",
};

const ROLE_ICONS: Record<string, string> = {
  product_manager: "📋",
  architect: "🏗️",
  api_designer: "🔌",
  project_manager: "📊",
  engineer: "💻",
  qa_engineer: "🧪",
  devops: "🚀",
  tech_writer: "📝",
};

type AgentStatus = "idle" | "working" | "typing" | "complete" | "failed";

interface AgentState {
  status: AgentStatus;
  duration?: number;
  docId?: string;
  error?: string;
  thinkingLines: string[];
}

interface Props {
  runId: string;
  onDocumentClick?: (docId: string) => void;
}

export function AgentDashboard({ runId, onDocumentClick }: Props) {
  const [agents, setAgents] = useState<Record<string, AgentState>>(() =>
    Object.fromEntries(AGENT_ORDER.map((n) => [n, { status: "idle" as AgentStatus, thinkingLines: [] }])),
  );
  const [runStatus, setRunStatus] = useState<string>("running");
  const [docIds, setDocIds] = useState<string[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const startTimesRef = useRef<Record<string, number>>({});
  const progressBarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const unsub = subscribeToRun(
      runId,
      (msg: WsMessage) => {
        if (msg.type === "status" && msg.data) {
          const d = msg.data as { status?: string; doc_ids?: string[] };
          if (d.status) setRunStatus(d.status);
          if (d.doc_ids) setDocIds(d.doc_ids);

          if (d.status === "complete") {
            setAgents((prev) => {
              const next = { ...prev };
              for (const name of AGENT_ORDER) {
                if (next[name]?.status !== "failed") {
                  next[name] = { ...next[name], status: "complete", thinkingLines: [] };
                }
              }
              return next;
            });
          }
        }

        // Thinking line: append to agent's thought list
        if (msg.type === "thinking" && msg.agent && msg.line) {
          const agent = msg.agent;
          setAgents((prev) => {
            const state = prev[agent] ?? { status: "idle" as AgentStatus, thinkingLines: [] };
            return {
              ...prev,
              [agent]: {
                ...state,
                thinkingLines: [...(state.thinkingLines ?? []).slice(-4), msg.line!],
              },
            };
          });
        }

        // doc_start: agent is now typing (after LLM finished)
        if (msg.type === "doc_start" && msg.agent) {
          setAgents((prev) => {
            const state = prev[msg.agent!] ?? { status: "idle" as AgentStatus, thinkingLines: [] };
            return { ...prev, [msg.agent!]: { ...state, status: "typing", thinkingLines: [] } };
          });
        }

        if (msg.type === "event" && msg.agent) {
          const agent = msg.agent;
          const event = msg.event ?? "";
          const payload = msg.payload ?? {};

          setAgents((prev) => {
            const next = { ...prev };
            const state = next[agent] ?? { status: "idle" as AgentStatus, thinkingLines: [] };

            if (event === "started") {
              startTimesRef.current[agent] = Date.now();
              next[agent] = { ...state, status: "working", thinkingLines: [] };
              setExpanded(agent); // auto-expand the working agent
            } else if (event === "completed") {
              const elapsed = startTimesRef.current[agent]
                ? (Date.now() - startTimesRef.current[agent]) / 1000
                : undefined;
              next[agent] = {
                status: "complete",
                duration: (payload.duration as number | undefined) ?? elapsed,
                docId: payload.doc_id as string | undefined,
                thinkingLines: [],
              };
              if (payload.doc_id) {
                setDocIds((ids) =>
                  ids.includes(payload.doc_id as string) ? ids : [...ids, payload.doc_id as string],
                );
              }
            } else if (event === "failed") {
              next[agent] = {
                status: "failed",
                error: payload.error as string | undefined,
                thinkingLines: [],
              };
            }
            return next;
          });
        }
      },
      () => setConnected(false),
    );

    setConnected(true);
    return unsub;
  }, [runId]);

  const completedCount = AGENT_ORDER.filter((n) => agents[n]?.status === "complete").length;
  const progressPct = Math.round((completedCount / AGENT_ORDER.length) * 100);

  useEffect(() => {
    if (progressBarRef.current) {
      progressBarRef.current.style.width = `${progressPct}%`;
    }
  }, [progressPct]);

  const statusColor: Record<AgentStatus, string> = {
    idle: "bg-gray-600",
    working: "bg-yellow-500 animate-pulse",
    typing: "bg-blue-500 animate-pulse",
    complete: "bg-green-500",
    failed: "bg-red-500",
  };

  const statusIcon: Record<AgentStatus, string> = {
    idle: "○",
    working: "💭",
    typing: "✍️",
    complete: "✓",
    failed: "✗",
  };

  return (
    <div className="p-4 bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-bold">Agents</h2>
        <span
          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
            connected ? "bg-green-500/20 text-green-400" : "bg-gray-600/20 text-gray-400"
          }`}
        >
          {connected ? "● Live" : "○ Off"}
        </span>
      </div>

      {/* Overall progress bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Progress</span>
          <span>{completedCount}/{AGENT_ORDER.length}</span>
        </div>
        <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
          <div
            ref={progressBarRef}
            className="h-full bg-blue-500 rounded-full transition-all duration-500"
          />
        </div>
      </div>

      {/* Agent list */}
      <div className="space-y-1.5">
        {AGENT_ORDER.map((name) => {
          const state = agents[name] ?? { status: "idle" as AgentStatus, thinkingLines: [] };
          const isExpanded = expanded === name;
          const isActive = state.status === "working" || state.status === "typing";

          return (
            <div
              key={name}
              className={`rounded-lg overflow-hidden border transition-colors ${
                isActive
                  ? "border-blue-500/40 bg-blue-950/20"
                  : "border-transparent bg-gray-800"
              }`}
            >
              <button
                type="button"
                className="w-full px-3 py-2.5 flex items-center gap-2.5 text-left hover:bg-gray-700/40 transition-colors"
                onClick={() => setExpanded(isExpanded ? null : name)}
              >
                <div
                  className={`w-6 h-6 rounded-full ${statusColor[state.status]} flex items-center justify-center flex-shrink-0`}
                >
                  <span className="text-xs font-bold">{statusIcon[state.status]}</span>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm">{ROLE_ICONS[name]}</span>
                    <span className="font-medium text-xs">{ROLE_LABELS[name] ?? name}</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5 truncate">
                    {state.status === "working"
                      ? "Thinking…"
                      : state.status === "typing"
                        ? "Writing doc…"
                        : state.status === "complete"
                          ? state.duration != null
                            ? `Done · ${state.duration.toFixed(1)}s`
                            : "Done"
                          : state.status === "failed"
                            ? "Failed"
                            : "Waiting"}
                  </p>
                </div>

                {state.docId && onDocumentClick && (
                  <button
                    type="button"
                    className="text-xs text-blue-400 hover:text-blue-300 px-1.5 py-0.5 rounded border border-blue-500/30 transition-colors"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDocumentClick(state.docId!);
                    }}
                  >
                    View
                  </button>
                )}
              </button>

              {/* Thinking lines — shown inline while agent is working */}
              {isActive && state.thinkingLines && state.thinkingLines.length > 0 && (
                <div className="px-3 pb-2.5 space-y-0.5">
                  {state.thinkingLines.map((line, i) => (
                    <div key={i} className="flex items-start gap-1.5 text-xs text-gray-400">
                      <span className="text-yellow-500/70 flex-shrink-0">›</span>
                      <span className="leading-relaxed">{line}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Expanded details (for completed agents) */}
              {isExpanded && !isActive && (
                <div className="px-3 pb-2.5 pt-1 border-t border-gray-700/40 text-xs text-gray-400 space-y-1">
                  <p>
                    <span className="text-gray-500">Status:</span>{" "}
                    <span className="text-white capitalize">{state.status}</span>
                  </p>
                  {state.duration != null && (
                    <p>
                      <span className="text-gray-500">Duration:</span>{" "}
                      <span className="text-white">{state.duration.toFixed(2)}s</span>
                    </p>
                  )}
                  {state.docId && (
                    <p>
                      <span className="text-gray-500">Doc ID:</span>{" "}
                      <span className="text-blue-400 font-mono text-xs">{state.docId.slice(0, 16)}…</span>
                    </p>
                  )}
                  {state.error && (
                    <p className="text-red-400">
                      <span className="text-gray-500">Error:</span> {state.error}
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-gray-800 flex justify-between text-xs text-gray-500">
        <span>{completedCount}/{AGENT_ORDER.length} complete</span>
        <span className="capitalize">{runStatus}</span>
      </div>

      {docIds.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-800">
          <p className="text-xs text-gray-500 mb-1.5">{docIds.length} doc(s) ready</p>
          <div className="flex flex-wrap gap-1">
            {docIds.slice(0, 6).map((id) => (
              <button
                key={id}
                type="button"
                className="text-xs px-2 py-0.5 bg-gray-700 hover:bg-gray-600 rounded font-mono truncate max-w-[90px] transition-colors"
                onClick={() => onDocumentClick?.(id)}
                title={id}
              >
                {id.slice(0, 8)}…
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
