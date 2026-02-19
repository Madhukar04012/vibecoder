/**
 * LiveDocPanel — real-time code generation viewer
 *
 * Shows two phases per agent:
 *  1. Thinking lines appear one by one while the LLM is generating
 *  2. Document content types character-by-character when the doc arrives
 */
import React, { useEffect, useRef, useState } from "react";
import { subscribeToRun, type WsMessage } from "@/lib/society-api";

const ROLE_LABELS: Record<string, string> = {
  product_manager: "Product Manager",
  architect: "Architect",
  api_designer: "API Designer",
  project_manager: "Project Manager",
  engineer: "Engineer",
  qa_engineer: "QA Engineer",
  devops: "DevOps",
  tech_writer: "Tech Writer",
  orchestrator: "Orchestrator",
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
  orchestrator: "🎯",
};

// ── Drain speed: 24 chars every 10ms ≈ 2 400 chars/sec ───────────────────
const DRAIN_CHARS = 24;
const DRAIN_MS = 10;

interface ThinkingLine {
  agent: string;
  line: string;
  key: number;
}

interface CompletedDoc {
  docId: string;
  title: string;
  agent: string;
  content: string;
}

interface Props {
  runId: string;
  onDocumentReady?: (docId: string) => void;
}

export function LiveDocPanel({ runId, onDocumentReady }: Props) {
  // ── Thinking state ────────────────────────────────────────────────────
  const [thinkingLines, setThinkingLines] = useState<ThinkingLine[]>([]);
  const lineCounterRef = useRef(0);

  // ── Active document being typed ───────────────────────────────────────
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [activeDocTitle, setActiveDocTitle] = useState<string>("");
  const [activeDocId, setActiveDocId] = useState<string>("");
  const [liveContent, setLiveContent] = useState<string>("");
  const bufferRef = useRef<string>("");
  const isTypingRef = useRef(false);

  // ── Skip button: flush buffer instantly ──────────────────────────────
  const skipTyping = () => {
    setLiveContent((prev) => prev + bufferRef.current);
    bufferRef.current = "";
    isTypingRef.current = false;
  };

  // ── Completed docs list ───────────────────────────────────────────────
  const [completedDocs, setCompletedDocs] = useState<CompletedDoc[]>([]);

  // ── Phase label for header ────────────────────────────────────────────
  const [phase, setPhase] = useState<"idle" | "thinking" | "typing" | "done">("idle");
  const [runDone, setRunDone] = useState(false);

  // ── Scroll refs ───────────────────────────────────────────────────────
  const thinkingEndRef = useRef<HTMLDivElement>(null);
  const codeEndRef = useRef<HTMLDivElement>(null);

  // ── Typewriter drain interval ─────────────────────────────────────────
  useEffect(() => {
    const timer = setInterval(() => {
      if (bufferRef.current.length === 0) return;
      const chunk = bufferRef.current.slice(0, DRAIN_CHARS);
      bufferRef.current = bufferRef.current.slice(DRAIN_CHARS);
      setLiveContent((prev) => prev + chunk);
    }, DRAIN_MS);
    return () => clearInterval(timer);
  }, []);

  // ── Auto-scroll code area during typing ──────────────────────────────
  useEffect(() => {
    codeEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [liveContent]);

  // ── Auto-scroll thinking area ─────────────────────────────────────────
  useEffect(() => {
    thinkingEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [thinkingLines]);

  // ── WebSocket subscription ────────────────────────────────────────────
  useEffect(() => {
    const unsub = subscribeToRun(runId, (msg: WsMessage) => {
      switch (msg.type) {
        case "thinking": {
          if (!msg.agent || !msg.line) break;
          setPhase("thinking");
          setActiveAgent(msg.agent);
          lineCounterRef.current += 1;
          setThinkingLines((prev) => [
            ...prev.slice(-40), // keep last 40 lines max
            { agent: msg.agent!, line: msg.line!, key: lineCounterRef.current },
          ]);
          break;
        }

        case "doc_start": {
          if (!msg.agent || !msg.doc_id) break;
          setPhase("typing");
          setActiveAgent(msg.agent);
          setActiveDocId(msg.doc_id);
          setActiveDocTitle(msg.title ?? "Document");
          setLiveContent("");
          bufferRef.current = "";
          isTypingRef.current = true;
          break;
        }

        case "doc_delta": {
          if (!msg.delta) break;
          bufferRef.current += msg.delta;
          break;
        }

        case "doc_end": {
          isTypingRef.current = false;
          // flush remaining buffer in one shot
          setLiveContent((prev) => prev + bufferRef.current);
          bufferRef.current = "";
          if (msg.doc_id) onDocumentReady?.(msg.doc_id);
          break;
        }

        case "event": {
          if (msg.event === "completed" && msg.agent && msg.payload?.doc_id) {
            const docId = msg.payload.doc_id as string;
            setCompletedDocs((prev) => [
              ...prev,
              {
                docId,
                title: activeDocTitle || "Document",
                agent: msg.agent!,
                content: "",
              },
            ]);
          }
          if (msg.event === "workflow_completed" || msg.event === "completed") {
            setPhase("done");
          }
          break;
        }

        case "status": {
          const d = msg.data as { status?: string } | undefined;
          if (d?.status === "complete" || d?.status === "failed") {
            setRunDone(true);
            setPhase("done");
          }
          break;
        }

        default:
          break;
      }
    });
    return unsub;
  }, [runId, activeDocTitle, onDocumentReady]);

  // ── Helpers ───────────────────────────────────────────────────────────
  const agentLabel = activeAgent ? (ROLE_LABELS[activeAgent] ?? activeAgent) : null;
  const agentIcon = activeAgent ? (ROLE_ICONS[activeAgent] ?? "🤖") : "";

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full bg-gray-950 text-white overflow-hidden">

      {/* ── Status bar ─────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 px-5 py-3 border-b border-gray-800 bg-gray-900/60 flex-shrink-0">
        {phase === "idle" && (
          <span className="text-gray-500 text-sm">Waiting for agents…</span>
        )}
        {phase === "thinking" && agentLabel && (
          <>
            <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse flex-shrink-0" />
            <span className="text-sm text-yellow-300 font-medium">
              {agentIcon} {agentLabel} is thinking…
            </span>
          </>
        )}
        {phase === "typing" && agentLabel && (
          <>
            <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse flex-shrink-0" />
            <span className="text-sm text-blue-300 font-medium">
              {agentIcon} {agentLabel} — writing <span className="text-white">{activeDocTitle}</span>
            </span>
            <button
              type="button"
              onClick={skipTyping}
              className="ml-auto text-xs text-gray-400 hover:text-white border border-gray-600 hover:border-gray-400 px-3 py-1 rounded-md transition-colors"
            >
              Skip typing ⏩
            </button>
          </>
        )}
        {phase === "done" && (
          <>
            <span className="w-2 h-2 rounded-full bg-green-400 flex-shrink-0" />
            <span className="text-sm text-green-300 font-medium">
              All agents complete — {completedDocs.length} document{completedDocs.length !== 1 ? "s" : ""} generated
            </span>
          </>
        )}
      </div>

      <div className="flex flex-col flex-1 overflow-hidden">

        {/* ── Thinking panel ──────────────────────────────────────── */}
        {thinkingLines.length > 0 && (
          <div className="flex-shrink-0 max-h-40 overflow-y-auto border-b border-gray-800 bg-gray-900/40 px-5 py-3">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              💭 Chain of thought
            </p>
            <div className="space-y-1">
              {thinkingLines.map((t) => (
                <div
                  key={t.key}
                  className="flex items-start gap-2 text-sm animate-fade-in"
                >
                  <span className="text-yellow-500 flex-shrink-0 mt-0.5 text-xs">▶</span>
                  <span className="text-gray-300">{t.line}</span>
                </div>
              ))}
              <div ref={thinkingEndRef} />
            </div>
          </div>
        )}

        {/* ── Live code area ───────────────────────────────────────── */}
        {(phase === "typing" || (phase === "done" && liveContent)) && (
          <div className="flex-1 overflow-hidden flex flex-col min-h-0">
            {activeDocTitle && (
              <div className="flex items-center gap-2 px-5 py-2 border-b border-gray-800 bg-gray-900/30 flex-shrink-0">
                <span className="text-xs text-gray-500">📄</span>
                <span className="text-xs font-medium text-gray-300">{activeDocTitle}</span>
                {isTypingRef.current && (
                  <span className="ml-auto text-xs text-blue-400 animate-pulse">typing…</span>
                )}
              </div>
            )}
            <pre className="flex-1 overflow-auto px-5 py-4 text-sm text-green-300 font-mono leading-relaxed whitespace-pre-wrap break-words bg-gray-950">
              {liveContent}
              {/* blinking cursor while typing */}
              {(isTypingRef.current || bufferRef.current.length > 0) && (
                <span className="inline-block w-2 h-4 bg-green-400 animate-blink align-text-bottom ml-0.5" />
              )}
              <div ref={codeEndRef} />
            </pre>
          </div>
        )}

        {/* ── Idle / completed docs list ────────────────────────────── */}
        {phase === "idle" && (
          <div className="flex-1 flex items-center justify-center text-gray-600">
            <div className="text-center">
              <div className="text-4xl mb-3">⚡</div>
              <p className="text-sm">Agents will appear here when the workflow starts</p>
            </div>
          </div>
        )}

        {/* ── Completed doc chips ──────────────────────────────────── */}
        {completedDocs.length > 0 && (
          <div className="flex-shrink-0 border-t border-gray-800 px-5 py-3 bg-gray-900/40">
            <p className="text-xs text-gray-500 mb-2 font-semibold uppercase tracking-wider">
              Generated documents
            </p>
            <div className="flex flex-wrap gap-2">
              {completedDocs.map((d) => (
                <button
                  key={d.docId}
                  type="button"
                  onClick={() => onDocumentReady?.(d.docId)}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-blue-500/50 rounded-full transition-colors"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0" />
                  {ROLE_ICONS[d.agent] ?? "📄"} {d.title}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
