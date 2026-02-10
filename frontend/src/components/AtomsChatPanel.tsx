/**
 * AtomsChatPanel - ATMOS Mode: Intent-Only Chat
 * 
 * ATMOS Rules:
 * - User types intent, hits Enter. That's it.
 * - NO suggestion chips
 * - NO action chips / approval flow  
 * - NO agent pipeline display
 * - NO diff review
 * - Chat shows minimal status: "Building…", "Live.", "Fixing issue…"
 */

import { useState, useCallback, useRef, useEffect, type KeyboardEvent } from "react";
import {
  Send, Loader2, Sparkles,
  RotateCcw, Trash2, Bot, User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useIDEStore, type ChatMessage } from "@/stores/ide-store";
import { EventBus } from "@/lib/event-bus";
import { runAtmosIntent, useAtmosStore } from "@/lib/atmos-state";
import { ChatTopBar } from "@/components/ChatTopBar";

// ─── Message Bubble ─────────────────────────────────────────────────────────

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  return (
    <div className={cn("px-4 py-1", isUser ? "flex justify-end" : "")}>
      <div className={cn(
        "max-w-[90%] rounded-2xl px-4 py-2.5 text-[13px] leading-relaxed",
        isUser
          ? "bg-indigo-600/20 text-white border border-indigo-500/15"
          : "bg-white/[0.03] text-white/80 border border-white/5"
      )}>
        <div className="flex items-center gap-2 mb-1">
          {isUser
            ? <User size={12} className="text-indigo-400" />
            : <Bot size={12} className="text-blue-400" />
          }
          <span className="text-[10px] font-bold uppercase tracking-wider text-white/30">
            {isUser ? 'You' : 'ATMOS'}
          </span>
          {message.isStreaming && (
            <Loader2 size={10} className="animate-spin text-blue-400 ml-auto" />
          )}
        </div>
        <div className="whitespace-pre-wrap break-words">{message.content}</div>

        {/* File badges */}
        {message.files && message.files.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2 pt-2 border-t border-white/5">
            {message.files.map((f) => (
              <span
                key={f.path}
                className={cn(
                  "inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium",
                  f.status === 'done'
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                )}
              >
                {f.path.split('/').pop()}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Component (ATMOS: wired to runAtmosIntent) ─────────────────────────────

export function AtomsChatPanel({ embedded }: { embedded?: boolean }) {
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    chatMessages, addChatMessage, updateLastAssistantMessage, appendToLastAssistantMessage,
    clearChat, setAIStatus, setProject, setWorkspaceMode, workspaceMode, aiStatus,
  } = useIDEStore();

  const atmosPhase = useAtmosStore((s) => s.phase);

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

  // ─── Listen for ATMOS events ────────────────────────────────────────────
  useEffect(() => {
    // Full chat messages from backend
    const offMsg = EventBus.on('AI_MESSAGE', (event) => {
      const { content } = event.payload as { content: string };
      if (content) {
        addChatMessage({
          role: 'assistant',
          content,
          isStreaming: false,
        });
      }
    });

    // Streaming tokens
    const offToken = EventBus.on('AI_MESSAGE_TOKEN', (event) => {
      const { token } = event.payload as { token: string };
      if (token) {
        appendToLastAssistantMessage(token);
      }
    });

    // Files created — track in last assistant message
    const offFile = EventBus.on('FILE_CREATED', (event) => {
      const { path } = event.payload as { path: string };
      const state = useIDEStore.getState();
      const msgs = [...state.chatMessages];
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === 'assistant') {
          const files = [...(msgs[i].files || [])];
          if (!files.find(f => f.path === path)) {
            files.push({ path, status: 'done' });
          }
          msgs[i] = { ...msgs[i], files };
          break;
        }
      }
      useIDEStore.setState({ chatMessages: msgs });
    });

    // Errors
    const offError = EventBus.on('AI_ERROR', (event) => {
      const { message } = event.payload as { message: string };
      addChatMessage({
        role: 'assistant',
        content: `⚠️ ${message}`,
        isStreaming: false,
      });
    });

    // Pipeline done
    const offDone = EventBus.on('ATMOS_DONE', () => {
      setIsStreaming(false);
      setAIStatus('idle');

      // Mark last assistant message as not streaming
      const state = useIDEStore.getState();
      const msgs = [...state.chatMessages];
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === 'assistant' && msgs[i].isStreaming) {
          msgs[i] = { ...msgs[i], isStreaming: false };
          break;
        }
      }
      useIDEStore.setState({ chatMessages: msgs });

      // If files were created, set project mode
      const hasFiles = Object.keys(state.fileContents).length > 0;
      if (hasFiles) {
        setProject({ id: 'generated', name: 'My Project' });
        setWorkspaceMode('project');
      }
    });

    return () => {
      offMsg();
      offToken();
      offFile();
      offError();
      offDone();
    };
  }, []);

  // ─── Send intent to ATMOS ───────────────────────────────────────────────
  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || isStreaming) return;

    // Add user message
    addChatMessage({ role: 'user', content: text });
    setInput("");
    setIsStreaming(true);
    setAIStatus('thinking');

    // Add streaming assistant placeholder
    addChatMessage({
      role: 'assistant',
      content: '',
      isStreaming: true,
      files: [],
    });

    // Fire the ATMOS pipeline — everything else is event-driven
    try {
      await runAtmosIntent(text);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      updateLastAssistantMessage(`Connection error: ${msg}. Make sure the backend is running.`);
      setAIStatus('error');
      setIsStreaming(false);
    }
  }, [input, isStreaming]);

  const handleStop = useCallback(() => {
    const ac = useAtmosStore.getState().abortController;
    if (ac) ac.abort();
    useAtmosStore.getState().reset();
    setIsStreaming(false);
    setAIStatus('idle');
  }, []);

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const isEmpty = chatMessages.length === 0 && workspaceMode === 'empty';

  return (
    <aside
      className={cn("flex flex-col h-full", embedded ? "w-full min-w-0" : "shrink-0")}
      style={embedded ? { background: "#111111" } : {
        width: "420px", minWidth: 340, maxWidth: 520,
        background: "#111111", borderRight: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      {/* Top Navigation Bar */}
      <ChatTopBar />

      {/* Minimal Header - just clear chat when active */}
      {chatMessages.length > 0 && (
        <div className="shrink-0 p-2 border-b border-white/5 flex justify-end">
          <button
            onClick={() => { clearChat(); useAtmosStore.getState().reset(); useIDEStore.getState().resetToEmptyWorkspace(); }}
            className="p-1.5 rounded-md hover:bg-white/5 text-white/30 hover:text-white/60 transition-colors"
            title="New chat"
          >
            <Trash2 size={14} />
          </button>
        </div>
      )}

      {/* Messages or Welcome */}
      <div className={cn(
        "flex-1 min-h-0",
        isEmpty ? "overflow-hidden" : "overflow-y-auto py-3 space-y-4"
      )}>
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full px-5">
            <h2 className="text-[22px] font-semibold text-white mb-2 tracking-tight">What do you want to build?</h2>
            <p className="text-[13px] text-white/40 text-center mb-8">
              Type your intent below. AI handles everything else.
            </p>
          </div>
        ) : (
          <>
            {chatMessages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Thinking indicator */}
            {isStreaming && atmosPhase === 'interpreting' && (
              <div className="flex items-center gap-2 px-5 text-[12px] text-gray-500">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span>Understanding your intent…</span>
              </div>
            )}

            {/* File generation indicator */}
            {isStreaming && atmosPhase === 'generating' && (
              <div className="flex items-center gap-2 px-5 text-[12px] text-blue-400">
                <Loader2 size={12} className="animate-spin" />
                <span>Writing code…</span>
              </div>
            )}

            {/* Building indicator */}
            {isStreaming && atmosPhase === 'building' && (
              <div className="flex items-center gap-2 px-5 text-[12px] text-amber-400">
                <Loader2 size={12} className="animate-spin" />
                <span>Installing dependencies…</span>
              </div>
            )}

            {/* Running indicator */}
            {isStreaming && atmosPhase === 'running' && (
              <div className="flex items-center gap-2 px-5 text-[12px] text-emerald-400">
                <Loader2 size={12} className="animate-spin" />
                <span>Starting dev server…</span>
              </div>
            )}
          </>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Simplified */}
      <div className="p-4 bg-[#0a0a0a] shrink-0 border-t border-white/5">
        <div
          className="relative rounded-lg border border-white/10 overflow-hidden transition-all focus-within:border-blue-500/50"
          style={{ background: '#141414' }}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            className="w-full bg-transparent text-[13px] text-white placeholder:text-white/30 caret-blue-400 outline-none resize-none px-4 py-3 leading-relaxed disabled:opacity-50"
            style={{ minHeight: '44px', maxHeight: '120px' }}
            placeholder="Ask the team to bring your idea to life"
          />
          <div className="absolute right-2 bottom-2 flex items-center gap-2">
            <span className="text-[10px] text-white/20">Enter to send</span>
            {isStreaming ? (
              <button
                onClick={handleStop}
                className="h-7 px-2.5 rounded-md flex items-center gap-1 text-[11px] bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors"
              >
                <RotateCcw size={11} />
                Stop
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="w-7 h-7 rounded-md flex items-center justify-center bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 transition-all duration-200 disabled:opacity-20 disabled:cursor-not-allowed border border-blue-500/20"
                title="Send"
              >
                <Send size={13} />
              </button>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
