/**
 * AgentChat — multi-agent chat panel (Mike, Alex, Iris, etc.)
 * Uses orchestrator, IDE tools, and ide-bridge for real file/terminal integration.
 */

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import { AgentOrchestrator, type Message } from "@/core/orchestrator";
import { AGENTS } from "@/agents/definitions";
import { useIDEStore } from "@/stores/ide-store";

interface PendingApproval {
  plan: string;
  onApprove: () => void;
}

export function AgentChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [stepCount, setStepCount] = useState(0);
  const [pendingApproval, setPendingApproval] = useState<PendingApproval | null>(null);
  const agentSteps = useIDEStore((s) => s.agentSteps);
  const orchestratorRef = useRef<AgentOrchestrator | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    orchestratorRef.current = new AgentOrchestrator(
      (msg) => {
        setMessages((prev) => [...prev, msg]);
      },
      () => {
        setStepCount((prev) => prev + 1);
      },
      (plan: string, onApprove: () => void) => {
        setPendingApproval({ plan, onApprove });
      }
    );
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isRunning) return;
    setIsRunning(true);
    const userInput = input;
    setInput("");
    await orchestratorRef.current?.handleUserMessage(userInput);
    setIsRunning(false);
  };

  const getAgentColor = (agent: string) => {
    const colors: Record<string, string> = {
      mike: "text-yellow-400 border-yellow-400",
      alex: "text-green-400 border-green-400",
      iris: "text-purple-400 border-purple-400",
      emma: "text-pink-400 border-pink-400",
      sarah: "text-blue-400 border-blue-400",
      user: "text-white border-gray-600",
    };
    return colors[agent] ?? "text-gray-400";
  };

  const getAgentRole = (agent: string) => AGENTS[agent]?.role ?? "User";

  const agentList = Object.values(AGENTS);

  return (
    <div
      className="flex flex-col h-full text-white"
      style={{ background: "var(--ide-chat-bg)", color: "var(--ide-text)" }}
    >
      <div
        className="flex gap-2 p-3 border-b shrink-0"
        style={{ borderColor: "var(--ide-border)" }}
      >
        {agentList.map((agent) => (
          <div
            key={agent.name}
            className="flex items-center gap-1 px-2 py-1 rounded-full border text-xs"
            style={{ borderColor: "var(--ide-border)" }}
          >
            <div className="w-2 h-2 rounded-full bg-green-400" />
            <span>{agent.name}</span>
            <span className="opacity-50">{agent.role}</span>
          </div>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.length === 0 && (
          <div className="text-center mt-20" style={{ color: "var(--ide-text-muted)" }}>
            <p className="text-xl mb-2">What do you want to build?</p>
            <p className="text-sm">Your AI team will collaborate to bring your vision to life.</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className="flex flex-col gap-1">
            {msg.agent !== "user" && (
              <div
                className={`flex items-center gap-2 text-xs font-bold ${getAgentColor(msg.agent)}`}
              >
                <div
                  className="w-6 h-6 rounded-full border flex items-center justify-center text-xs border-current"
                >
                  {msg.agent[0].toUpperCase()}
                </div>
                <span>{msg.agent.charAt(0).toUpperCase() + msg.agent.slice(1)}</span>
                <span className="opacity-50 font-normal">{getAgentRole(msg.agent)}</span>
              </div>
            )}
            <div
              className={`rounded-lg p-3 text-sm leading-relaxed ${
                msg.agent === "user"
                  ? "ml-auto max-w-[80%]"
                  : "max-w-[95%]"
              }`}
              style={{
                background: msg.agent === "user" ? "var(--ide-surface-hover)" : "var(--ide-surface)",
              }}
            >
              <div className="agent-chat-markdown [&_pre]:whitespace-pre-wrap [&_code]:bg-black/30 [&_code]:px-1 [&_code]:rounded [&_ul]:list-disc [&_ul]:pl-4 [&_ol]:list-decimal [&_ol]:pl-4">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeSanitize]}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        ))}

        {isRunning && (
          <div className="flex flex-col gap-2">
            <div
              className="flex items-center gap-2 text-sm"
              style={{ color: "var(--ide-text-muted)" }}
            >
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full animate-bounce bg-current opacity-70" />
                <div className="w-2 h-2 rounded-full animate-bounce bg-current opacity-70 [animation-delay:0.1s]" />
                <div className="w-2 h-2 rounded-full animate-bounce bg-current opacity-70 [animation-delay:0.2s]" />
              </div>
              <span>Agents working...</span>
              {stepCount > 0 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-white/10">
                  Processed {stepCount} step{stepCount !== 1 ? "s" : ""}
                </span>
              )}
            </div>
          </div>
        )}

        {pendingApproval && (
          <div
            className="rounded-lg p-4 border"
            style={{
              background: "var(--ide-surface)",
              borderColor: "rgba(234, 179, 8, 0.4)",
            }}
          >
            <p className="text-yellow-400 text-xs font-bold mb-2 uppercase tracking-wide">
              📋 Mike has created a plan — review before proceeding
            </p>
            <pre
              className="text-xs mb-3 whitespace-pre-wrap leading-relaxed"
              style={{ color: "var(--ide-text-muted)" }}
            >
              {pendingApproval.plan}
            </pre>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setStepCount(0);
                  pendingApproval.onApprove();
                  setPendingApproval(null);
                }}
                className="px-4 py-2 bg-yellow-500 text-black rounded-lg text-xs font-bold hover:bg-yellow-400 transition-colors"
              >
                ✅ Approve Plan
              </button>
              <button
                type="button"
                onClick={() => setPendingApproval(null)}
                className="px-4 py-2 rounded-lg text-xs font-medium hover:bg-white/10 transition-colors"
                style={{ color: "var(--ide-text-muted)" }}
              >
                ✕ Cancel
              </button>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="p-4 border-t shrink-0" style={{ borderColor: "var(--ide-border)" }}>
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Ask AI…"
            className="flex-1 rounded-lg px-4 py-3 text-sm resize-none outline-none border border-transparent transition-colors focus:border-blue-500"
            style={{ background: "var(--ide-surface)", color: "var(--ide-text)" }}
            rows={3}
            disabled={isRunning}
          />
          <button
            type="button"
            onClick={sendMessage}
            disabled={isRunning || !input.trim()}
            className="px-4 py-2 bg-blue-600 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
          >
            Send
          </button>
        </div>
        <p className="text-xs mt-2" style={{ color: "var(--ide-text-muted)" }}>
          Enter to send · Shift+Enter new line · @alex @iris to mention
        </p>
      </div>
    </div>
  );
}
