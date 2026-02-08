/**
 * AtomsChatPanel - AI Chat with Streaming Code Generation
 * Cursor/Bolt-style: AI writes code directly into the IDE
 */

import { useState, useCallback, useRef, useEffect, type KeyboardEvent } from "react";
import {
  Send, Loader2, Sparkles, FileCode, Check, ChevronRight,
  RotateCcw, Copy, Trash2, Bot, User, Zap,
  Brain, Map, Code2, CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useIDEStore, type ChatMessage } from "@/stores/ide-store";
import { getApiUrl } from "@/lib/api";
import { EventBus } from "@/lib/event-bus";
import { VFS } from "@/lib/virtual-fs";
import { DiffReviewPanel } from "@/components/DiffReviewPanel";

// ─── Suggestions ────────────────────────────────────────────────────────────

const SUGGESTIONS = [
  { label: "Create a React app", prompt: "Create a React app with Vite, a counter component, and modern styling" },
  { label: "Build a todo app", prompt: "Build a todo app with React, local state, add/delete/complete features, and a clean UI" },
  { label: "Create a landing page", prompt: "Create a modern landing page with a hero section, features grid, and footer" },
  { label: "Build a REST API", prompt: "Build a Python FastAPI REST API with CRUD endpoints, models, and error handling" },
  { label: "Full-stack app", prompt: "Create a full-stack app with React frontend and FastAPI backend with user authentication" },
  { label: "Dashboard UI", prompt: "Create a dashboard with stats cards, a chart area, and a data table using React" },
];

// ─── Stream Parser ──────────────────────────────────────────────────────────

interface StreamEvent {
  type: 'thinking' | 'message' | 'message_token' | 'file_start' | 'file_content' | 'file_end' | 'done' | 'error';
  [key: string]: unknown;
}

function parseSSE(line: string): StreamEvent | null {
  if (!line.startsWith('data: ')) return null;
  try {
    return JSON.parse(line.slice(6));
  } catch {
    return null;
  }
}

// ─── File Creation Item ─────────────────────────────────────────────────────

function FileItem({ path, status }: { path: string; status: 'pending' | 'generating' | 'done' }) {
  const openFile = useIDEStore((s) => s.openFile);

  return (
    <div
      className={cn(
        "flex items-center gap-2 px-3 py-1.5 rounded-md text-[12px] transition-all duration-300 cursor-pointer",
        status === 'done' && "hover:bg-[#2a2a2a]",
        status === 'generating' && "bg-[#1a2332] border border-blue-500/20",
        status === 'pending' && "opacity-50",
      )}
      onClick={() => status === 'done' && openFile(path)}
    >
      {status === 'generating' ? (
        <Loader2 size={12} className="animate-spin text-blue-400 shrink-0" />
      ) : status === 'done' ? (
        <Check size={12} className="text-emerald-400 shrink-0" />
      ) : (
        <FileCode size={12} className="text-gray-500 shrink-0" />
      )}
      <span className={cn(
        "truncate font-mono",
        status === 'done' && "text-emerald-300",
        status === 'generating' && "text-blue-300",
        status === 'pending' && "text-gray-500",
      )}>
        {path}
      </span>
      {status === 'done' && (
        <ChevronRight size={10} className="ml-auto text-gray-500 shrink-0" />
      )}
    </div>
  );
}

// ─── Message Bubble ─────────────────────────────────────────────────────────

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const isDiscussion = message.role === 'system';
  const [copied, setCopied] = useState(false);

  // Agent discussions: compact inline style
  if (isDiscussion) {
    return (
      <div className="flex gap-2 px-4 py-0.5">
        <div className="w-4 flex items-center justify-center shrink-0">
          <div className="w-1 h-1 rounded-full bg-gray-600" />
        </div>
        <div className="text-[11px] text-gray-500 leading-relaxed">
          {message.content.replace(/\*\*/g, '')}
        </div>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn("group flex gap-2.5 px-3", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div className={cn(
        "w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5",
        isUser ? "bg-blue-600/20" : "bg-emerald-600/15 border border-emerald-500/20",
      )}>
        {isUser ? (
          <User size={14} className="text-blue-400" />
        ) : (
          <Bot size={14} className="text-emerald-400" />
        )}
      </div>

      {/* Content */}
      <div className={cn("flex flex-col gap-1 max-w-[85%] min-w-0", isUser ? "items-end" : "items-start")}>
        <div className={cn(
          "rounded-xl px-3.5 py-2.5 text-[13px] leading-relaxed break-words",
          isUser
            ? "bg-blue-600/15 text-gray-100 border border-blue-500/15"
            : "bg-[#1a1a1a] text-gray-200 border border-[#2a2a2a]",
        )}>
          {message.content}
          {message.isStreaming && (
            <span className="inline-block w-1.5 h-4 bg-blue-400 ml-0.5 animate-pulse rounded-sm" />
          )}
        </div>

        {/* File list */}
        {message.files && message.files.length > 0 && (
          <div className="w-full bg-[#111] rounded-lg border border-[#222] py-1.5 px-1 space-y-0.5 mt-1">
            <div className="px-2 py-1 text-[11px] text-gray-500 font-medium uppercase tracking-wider">
              Files ({message.files.length})
            </div>
            {message.files.map((f) => (
              <FileItem key={f.path} path={f.path} status={f.status} />
            ))}
          </div>
        )}

        {/* Actions */}
        {!isUser && !message.isStreaming && message.content && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={handleCopy}
              className="p-1 rounded hover:bg-[#2a2a2a] text-gray-500 hover:text-gray-300 transition-colors"
              title="Copy"
            >
              {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Component ──────────────────────────────────────────────────────────────

// ─── Agent Pipeline ─────────────────────────────────────────────────────

const AGENT_ICONS: Record<string, React.ReactNode> = { brain: <Brain size={12} />, map: <Map size={12} />, code: <Code2 size={12} /> };

function AgentPipeline() {
  const steps = useIDEStore((s) => s.agentSteps);
  if (steps.length === 0) return null;
  return (
    <div className="mx-3 mb-2 rounded-lg border border-[#222] bg-[#0f0f0f] overflow-hidden">
      <div className="px-3 py-1.5 text-[10px] text-gray-500 uppercase tracking-wider font-medium border-b border-[#1a1a1a]">Agent Pipeline</div>
      {steps.map((step) => (
        <div key={step.id} className={cn("flex items-center gap-2 px-3 py-2 text-[12px] border-b border-[#1a1a1a] last:border-b-0", step.status === 'running' && "bg-blue-500/5")}>
          <div className={cn("w-5 h-5 rounded-md flex items-center justify-center shrink-0", step.status === 'running' ? "bg-blue-500/15 text-blue-400" : "bg-emerald-500/15 text-emerald-400")}>
            {step.status === 'running' ? <Loader2 size={11} className="animate-spin" /> : <CheckCircle2 size={11} />}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <span className={step.status === 'running' ? "text-blue-300 shrink-0" : "text-emerald-300 shrink-0"}>{AGENT_ICONS[step.icon] || <Sparkles size={12} />}</span>
              <span className="font-medium text-gray-300">{step.name}</span>
              {step.status === 'running' && <span className="text-gray-500 truncate">{step.description}</span>}
            </div>
            {step.status === 'done' && step.result && <div className="text-[11px] text-gray-500 truncate mt-0.5">{step.result}</div>}
          </div>
        </div>
      ))}
    </div>
  );
}

export type AtomsMode = 'standard' | 'race';

export function AtomsChatPanel({ embedded }: { embedded?: boolean }) {
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [mode, setMode] = useState<AtomsMode>('standard');
  const [raceStatus, setRaceStatus] = useState<{ teams: number; results: Record<number, { status: string; score?: number; phase?: string }> } | null>(null);
  const [blackboard, setBlackboard] = useState<Record<string, unknown>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const {
    chatMessages, addChatMessage, updateLastAssistantMessage, appendToLastAssistantMessage,
    clearChat, createFile, appendToFile, setFileLiveWriting, openFile,
    setAIStatus, setAICurrentFile, setAIFileProgress,
    addActivity, setProject, setWorkspaceMode, fileContents, workspaceMode, aiStatus,
    addAgentStep, completeAgentStep, clearAgentSteps, agentSteps,
  } = useIDEStore();

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, aiStatus]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
    }
  }, [input]);

  // ─── Stream handler ────────────────────────────────────────────────────
  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || isStreaming) return;

    // Add user message
    addChatMessage({ role: 'user', content: text });
    setInput("");
    setIsStreaming(true);
    setAIStatus('thinking');

    // Add assistant placeholder
    addChatMessage({ role: 'assistant', content: '', isStreaming: true, files: [] });
    clearAgentSteps();

    const controller = new AbortController();
    abortRef.current = controller;

    const fileTracker: { path: string; status: 'pending' | 'generating' | 'done' }[] = [];
    let fullContent = '';
    let firstFileOpened = false;

    const updateAssistantFiles = () => {
      const s = useIDEStore.getState();
      const msgs = [...s.chatMessages];
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === 'assistant') {
          msgs[i] = { ...msgs[i], files: [...fileTracker] };
          break;
        }
      }
      useIDEStore.setState({ chatMessages: msgs });
    };

    try {
      const endpoint = mode === 'race' ? "/api/atoms/stream" : "/api/atoms/stream";
      const res = await fetch(getApiUrl(endpoint), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text, files: fileContents, mode, race_teams: 2 }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No reader");

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const ev = parseSSE(line);
          if (!ev) continue;

          switch (ev.type) {
            // ── Agent pipeline ──────────────────────────────
            case 'agent_start': {
              addAgentStep({
                agent: ev.agent as string,
                name: ev.name as string,
                icon: ev.icon as string,
                description: ev.description as string,
              });
              setAIStatus('thinking');
              addActivity(`${ev.name}: ${ev.description}`, undefined, undefined, 'thinking');
              EventBus.emit('AI_AGENT_START', { agent: ev.agent, name: ev.name, icon: ev.icon, description: ev.description }, 'chat');
              break;
            }
            case 'agent_end': {
              completeAgentStep(ev.agent as string, ev.result as string);
              addActivity(`${ev.agent} done`, ev.result as string, true, 'message');
              EventBus.emit('AI_AGENT_END', { agent: ev.agent, result: ev.result }, 'chat');
              break;
            }

            // ── Thinking ────────────────────────────────────
            case 'thinking': {
              setAIStatus('thinking');
              addActivity('Thinking', ev.message as string, undefined, 'thinking');
              break;
            }

            // ── Chat messages ───────────────────────────────
            case 'message': {
              fullContent = ev.content as string;
              updateLastAssistantMessage(fullContent);
              setAIStatus('streaming');
              break;
            }
            case 'message_token': {
              fullContent += ev.token as string;
              appendToLastAssistantMessage(ev.token as string);
              setAIStatus('streaming');
              break;
            }

            // ── File: create empty + start live writing ─────
            case 'file_start': {
              const path = ev.path as string;
              const index = ev.index as number;
              const total = ev.total as number;

              setAIStatus('generating');
              setAICurrentFile(path);
              setAIFileProgress(index, total);

              // Create empty file and mark it as live-writing
              createFile(path, '', true);
              setFileLiveWriting(path, true);

              // Switch editor to this file
              openFile(path);
              firstFileOpened = true;

              fileTracker.push({ path, status: 'generating' });
              updateAssistantFiles();
              addActivity(`Writing ${path}`, `File ${index}/${total}`, undefined, 'file_create');
              EventBus.emit('AI_FILE_WRITING', { path }, 'chat');
              break;
            }

            // ── File: live character delta (THE KEY EVENT) ──
            case 'file_delta': {
              const path = ev.path as string;
              const delta = ev.delta as string;
              appendToFile(path, delta);
              VFS.append(path, delta); // Sync to Virtual FS
              EventBus.emit('AI_FILE_DELTA', { path, content: delta }, 'chat');
              break;
            }

            // ── File: old-style full content (backwards compat)
            case 'file_content': {
              const path = ev.path as string;
              const content = ev.content as string;
              createFile(path, content, true);
              if (!firstFileOpened) { openFile(path); firstFileOpened = true; }
              break;
            }

            // ── File: complete ──────────────────────────────
            case 'file_end': {
              const path = ev.path as string;
              setFileLiveWriting(path, false);
              const fi = fileTracker.findIndex((f) => f.path === path);
              if (fi !== -1) fileTracker[fi].status = 'done';
              updateAssistantFiles();
              addActivity(`Created ${path}`, undefined, true, 'file_create');
              EventBus.emit('AI_FILE_COMPLETE', { path }, 'chat');
              break;
            }

            // ── Done ────────────────────────────────────────
            case 'done': {
              setAIStatus('done');
              setAICurrentFile(null);

              const s3 = useIDEStore.getState();
              const m3 = [...s3.chatMessages];
              for (let i = m3.length - 1; i >= 0; i--) {
                if (m3[i].role === 'assistant') { m3[i] = { ...m3[i], isStreaming: false }; break; }
              }
              useIDEStore.setState({ chatMessages: m3 });

              if (fileTracker.length > 0) {
                setProject({ id: 'generated', name: 'My Project' });
                setWorkspaceMode('project');
                VFS.setProjectName('My Project');
                EventBus.emit('PROJECT_CREATED', { name: 'My Project', files: fileTracker.length }, 'chat');
              }
              EventBus.emit('AI_DONE', {}, 'chat');
              break;
            }

            // ── Blackboard updates ──────────────────────────
            case 'blackboard_update': {
              const field = ev.field as string;
              const value = ev.value;
              setBlackboard((prev) => ({ ...prev, [field]: value }));
              break;
            }

            // ── Race Mode events ────────────────────────────
            case 'race_start': {
              const teams = ev.teams as number;
              setRaceStatus({ teams, results: {} });
              addActivity(`Race Mode: ${teams} teams`, undefined, undefined, 'thinking');
              break;
            }
            case 'race_progress': {
              const team = ev.team as number;
              setRaceStatus((prev) => prev ? {
                ...prev,
                results: { ...prev.results, [team]: { status: ev.status as string, score: ev.score as number | undefined, phase: ev.phase as string | undefined } },
              } : null);
              break;
            }
            case 'race_result': {
              const winner = ev.winner as number;
              const score = ev.score as number;
              addActivity(`Race winner: Team ${winner}`, `Score: ${score}`, true, 'message');
              break;
            }

            // ── Preview ready (auto-deploy) ─────────────────
            case 'preview_ready': {
              const url = ev.url as string;
              EventBus.emit('PREVIEW_READY', { url }, 'chat');
              addActivity('Preview ready', url, true, 'message');
              break;
            }

            // ── Agent discussion (inter-agent chat) ─────────
            case 'discussion': {
              const from = ev.from as string;
              const to = ev.to as string;
              const msg = ev.message as string;
              const icon = ev.icon as string;
              addChatMessage({
                role: 'system',
                content: `**${from}** → ${to}: ${msg}`,
              });
              addActivity(`${from} → ${to}`, msg, undefined, 'message');
              break;
            }

            // ── Error ───────────────────────────────────────
            case 'error': {
              updateLastAssistantMessage(`Error: ${ev.message}`);
              setAIStatus('error');
              addActivity('Error', ev.message as string, false, 'error');
              break;
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        const msg = err instanceof Error ? err.message : String(err);
        updateLastAssistantMessage(`Connection error: ${msg}. Make sure the backend is running.`);
        setAIStatus('error');
      }
    } finally {
      setIsStreaming(false);
      setAIStatus('idle');
      abortRef.current = null;
    }
  }, [input, isStreaming, fileContents]);

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
    setAIStatus('idle');
  }, []);

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleSuggestion = (prompt: string) => {
    setInput(prompt);
    // Focus and auto-send
    setTimeout(() => {
      textareaRef.current?.focus();
    }, 50);
  };

  const isEmpty = chatMessages.length === 0 && workspaceMode === 'empty';

  return (
    <aside
      className={cn("flex flex-col h-full", embedded ? "w-full min-w-0" : "shrink-0")}
      style={embedded ? { background: "#111" } : {
        width: "42%", minWidth: 360, maxWidth: 520,
        background: "#111", borderRight: "1px solid #222",
      }}
    >
      {/* Header */}
      <div className="shrink-0 px-3 py-2 flex items-center justify-between border-b border-[#222]">
        <div className="flex items-center gap-2 text-[13px]">
          <div className="w-6 h-6 rounded-md bg-gradient-to-br from-blue-500/20 to-emerald-500/20 flex items-center justify-center border border-blue-500/20">
            <Sparkles size={12} className="text-blue-400" />
          </div>
          <span className="text-gray-300 font-medium">AI Assistant</span>
          {isStreaming && (
            <span className="flex items-center gap-1 text-[11px] text-blue-400">
              <Loader2 size={10} className="animate-spin" />
              {aiStatus === 'thinking' ? 'Thinking...' : aiStatus === 'generating' ? 'Generating...' : 'Writing...'}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {chatMessages.length > 0 && (
            <button
              onClick={() => { clearChat(); useIDEStore.getState().resetToEmptyWorkspace(); }}
              className="p-1.5 rounded-md hover:bg-[#2a2a2a] text-gray-500 hover:text-gray-300 transition-colors"
              title="New chat"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Messages or Welcome */}
      <div className="flex-1 overflow-y-auto min-h-0 py-3 space-y-4">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full px-4">
            {/* Logo */}
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/10 to-emerald-500/10 border border-[#2a2a2a] flex items-center justify-center mb-6">
              <Zap size={28} className="text-blue-400/80" />
            </div>

            <h2 className="text-[18px] font-semibold text-gray-200 mb-1">What do you want to build?</h2>
            <p className="text-[13px] text-gray-500 mb-6 text-center">
              Describe your project and I'll generate the code for you.
            </p>

            {/* Suggestions */}
            <div className="w-full space-y-2 max-w-sm">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => handleSuggestion(s.prompt)}
                  className="w-full text-left px-3 py-2.5 rounded-lg bg-[#1a1a1a] border border-[#252525] hover:border-[#333] hover:bg-[#1e1e1e] text-[13px] text-gray-300 transition-all duration-200 group flex items-center gap-2"
                >
                  <ChevronRight size={14} className="text-gray-600 group-hover:text-blue-400 transition-colors shrink-0" />
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {chatMessages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Thinking indicator */}
            {isStreaming && aiStatus === 'thinking' && (
              <div className="flex items-center gap-2 px-5 text-[12px] text-gray-500">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span>Analyzing your request...</span>
              </div>
            )}
          </>
        )}

        {/* Agent Pipeline */}
        <AgentPipeline />

        {/* Race Mode Status */}
        {raceStatus && (
          <div className="mx-3 mb-2 rounded-lg border border-amber-500/15 bg-[#0f0f0f] overflow-hidden">
            <div className="px-3 py-1.5 text-[10px] text-amber-400 uppercase tracking-wider font-medium border-b border-[#1a1a1a] flex items-center gap-1.5">
              <span>🏁</span> Race Mode — {raceStatus.teams} Teams
            </div>
            {Object.entries(raceStatus.results).map(([team, info]) => (
              <div key={team} className="flex items-center gap-2 px-3 py-2 text-[12px] border-b border-[#1a1a1a] last:border-0">
                <span className="font-medium text-gray-300">Team {team}</span>
                <span className={cn(
                  "px-1.5 py-0.5 rounded text-[10px]",
                  info.status === 'scored' ? "bg-emerald-500/15 text-emerald-400" :
                  info.status === 'complete' ? "bg-blue-500/15 text-blue-400" :
                  "bg-gray-500/10 text-gray-500",
                )}>
                  {info.status === 'scored' ? `Score: ${info.score}` : info.status === 'complete' ? 'Complete' : info.phase || 'Working...'}
                </span>
                {info.status === 'generating' && <Loader2 size={10} className="animate-spin text-blue-400" />}
              </div>
            ))}
          </div>
        )}

        {/* Diff Review (Atmos-style: user approves AI changes) */}
        <DiffReviewPanel />

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-3 py-3 shrink-0 border-t border-[#1a1a1a]">
        <div
          className="flex flex-col rounded-xl overflow-hidden w-full transition-all duration-200 focus-within:ring-1 focus-within:ring-blue-500/30 border border-[#2a2a2a] focus-within:border-blue-500/30"
          style={{ background: "#1a1a1a" }}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            className="w-full bg-transparent text-[13px] text-gray-100 placeholder:text-gray-500 caret-blue-400 outline-none resize-none px-4 pt-3 pb-1 leading-relaxed disabled:opacity-50"
            style={{ minHeight: '36px', maxHeight: '150px' }}
            placeholder={isStreaming ? "AI is working..." : "Describe what you want to build..."}
          />
          <div className="flex items-center justify-between px-3 pb-2 pt-1">
            <div className="flex items-center gap-2">
              {/* Mode Toggle */}
              <button
                onClick={() => setMode(mode === 'standard' ? 'race' : 'standard')}
                disabled={isStreaming}
                className={cn(
                  "flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium transition-all border",
                  mode === 'race'
                    ? "bg-amber-500/15 border-amber-500/25 text-amber-300"
                    : "bg-[#1e1e1e] border-[#2a2a2a] text-gray-500 hover:text-gray-400",
                )}
                title={mode === 'race' ? 'Race Mode: 2 teams compete' : 'Standard: single team'}
              >
                {mode === 'race' ? '🏁 Race' : '⚡ Standard'}
              </button>
              <span className="text-[10px] text-gray-600">Enter to send</span>
            </div>
            {isStreaming ? (
              <button
                onClick={handleStop}
                className="h-7 px-3 rounded-lg flex items-center gap-1.5 text-[12px] bg-red-500/15 text-red-400 border border-red-500/20 hover:bg-red-500/25 transition-colors"
              >
                <RotateCcw size={12} />
                Stop
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="h-7 w-7 rounded-lg flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-blue-600"
                title="Send message"
                aria-label="Send message"
              >
                <Send size={14} />
              </button>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
