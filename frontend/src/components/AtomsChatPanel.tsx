/**
 * AtomsChatPanel - Multi-Agent Chat
 * 
 * Professional chat interface for AI agent collaboration:
 * - Team Lead assigns work
 * - Product Manager writes requirements
 * - Architect designs the system
 * - Engineer writes code
 * - QA tests and reviews
 * - DevOps deploys
 */

import { useState, useCallback, useRef, useEffect, type KeyboardEvent } from "react";
import {
  Loader2,
  RotateCcw, User,
  Crown, ClipboardList, Layers, Code2, Shield, Rocket,
  Brain, ArrowRight, CheckCircle2, Activity,
  Plus, Paperclip, X, Upload,
  Sparkles, Zap, Globe, Database, MessageSquare,
  Play, Settings, FileCode, Search,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useIDEStore, type ChatMessage } from "@/stores/ide-store";
import { EventBus } from "@/lib/event-bus";
import { runAtmosIntent, useAtmosStore } from "@/lib/atmos-state";
import { ChatTopBar } from "@/components/ChatTopBar";
import { liveWriter } from "@/lib/live-writer";
import { apiFetch } from "@/lib/api";

// ─── Agent Icons ────────────────────────────────────────────────────────────

const AGENT_ICONS: Record<string, typeof Crown> = {
  crown: Crown,
  clipboard: ClipboardList,
  layers: Layers,
  code: Code2,
  shield: Shield,
  rocket: Rocket,
  brain: Brain,
  map: Brain,
  scale: Shield,
};

const AGENT_COLORS: Record<string, string> = {
  'Team Leader': 'text-amber-400',
  'Product Manager': 'text-purple-400',
  'Architect': 'text-cyan-400',
  'Engineer': 'text-green-400',
  'QA Engineer': 'text-orange-400',
  'DevOps': 'text-rose-400',
  'Planner': 'text-indigo-400',
};

const AGENT_BG_COLORS: Record<string, string> = {
  'Team Leader': 'border-amber-500/30 bg-amber-500/10',
  'Product Manager': 'border-purple-500/30 bg-purple-500/10',
  'Architect': 'border-cyan-500/30 bg-cyan-500/10',
  'Engineer': 'border-green-500/30 bg-green-500/10',
  'QA Engineer': 'border-orange-500/30 bg-orange-500/10',
  'DevOps': 'border-rose-500/30 bg-rose-500/10',
  'Planner': 'border-indigo-500/30 bg-indigo-500/10',
};

// ─── Example Prompts ────────────────────────────────────────────────────────

const EXAMPLE_PROMPTS = [
  {
    icon: Globe,
    title: "Build a landing page",
    prompt: "Create a modern landing page for a SaaS product with hero section, features, pricing, and contact form",
    color: "text-blue-400",
  },
  {
    icon: Database,
    title: "Create a REST API",
    prompt: "Build a REST API for a blog with user authentication, posts, and comments using FastAPI",
    color: "text-green-400",
  },
  {
    icon: Zap,
    title: "Todo app with auth",
    prompt: "Create a full-stack todo application with user authentication and persistent storage",
    color: "text-amber-400",
  },
  {
    icon: MessageSquare,
    title: "Real-time chat app",
    prompt: "Build a real-time chat application with WebSocket support and message history",
    color: "text-purple-400",
  },
];

// ─── Attachment Types ───────────────────────────────────────────────────────────

export interface ChatAttachment {
  id: string;
  name: string;
  type: 'file' | 'image' | 'code' | 'text';
  content: string;
  size: number;
  preview?: string;
}

function getAgentIcon(iconName?: string) {
  if (!iconName) return Brain;
  return AGENT_ICONS[iconName] || Brain;
}

function getAgentColor(name?: string) {
  if (!name) return 'text-blue-400';
  return AGENT_COLORS[name] || 'text-blue-400';
}

function getAgentBgColor(name?: string) {
  if (!name) return 'border-var(--ide-border) bg-var(--ide-surface)';
  return AGENT_BG_COLORS[name] || 'border-var(--ide-border) bg-var(--ide-surface)';
}

// ─── Discussion Bubble (Agent-to-Agent) ─────────────────────────────────────

function DiscussionBubble({ message }: { message: ChatMessage }) {
  const IconComp = getAgentIcon(message.agentIcon);
  const color = getAgentColor(message.agentName);
  const bgColor = getAgentBgColor(message.agentName);

  return (
    <div className="px-4 py-2">
      <div className={cn("max-w-[95%] rounded-2xl px-4 py-3 text-[13px] leading-relaxed border shadow-sm", bgColor)}>
        <div className="flex items-center gap-2 mb-2">
          <div className={cn("w-6 h-6 rounded-full flex items-center justify-center", bgColor)}>
            <IconComp size={14} className={color} />
          </div>
          <span className={cn("text-[12px] font-semibold", color)}>
            {message.agentName}
          </span>
          {message.toAgent && (
            <>
              <ArrowRight size={12} style={{ color: 'var(--ide-text-muted)' }} />
              <span className="text-[12px] font-medium" style={{ color: 'var(--ide-text-muted)' }}>
                {message.toAgent}
              </span>
            </>
          )}
        </div>
        <div className="whitespace-pre-wrap break-words pl-8" style={{ color: 'var(--ide-text)' }}>{message.content}</div>
      </div>
    </div>
  );
}

// ─── Agent Status Bubble ────────────────────────────────────────────────────

function AgentStatusBubble({ message }: { message: ChatMessage }) {
  const IconComp = getAgentIcon(message.agentIcon);
  const color = getAgentColor(message.agentName);
  const isResult = message.messageType === 'agent_result';

  return (
    <div className="px-4 py-1.5">
      <div className="flex items-center gap-3 text-[13px] px-4 py-2 rounded-xl" style={{ background: 'var(--ide-surface)' }}>
        <div className={cn("w-7 h-7 rounded-full flex items-center justify-center", isResult ? "bg-green-500/20" : "bg-blue-500/20")}>
          {isResult ? (
            <CheckCircle2 size={14} className="text-green-400" />
          ) : (
            <Activity size={14} className={cn(color, "animate-pulse")} />
          )}
        </div>
        <div className="flex items-center gap-2">
          <IconComp size={14} className={color} />
          <span className={cn("font-semibold", color)}>{message.agentName}</span>
        </div>
        <span style={{ color: 'var(--ide-text)' }}>{message.content}</span>
      </div>
    </div>
  );
}

// ─── Event Card Icons ────────────────────────────────────────────────────────

const EVENT_ICONS: Record<string, typeof Brain> = {
  run_started: Play,
  budget_configured: Settings,
  execution_plan: FileCode,
  project_analyzed: Search,
  stack_detected: Layers,
  architecture_designed: Layers,
  file_plan_ready: FileCode,
  qa_complete: Shield,
  state_transition: Activity,
  team_lead_started: Crown,
  pm_started: ClipboardList,
  architect_started: Layers,
  engineer_started: Code2,
  qa_started: Shield,
  devops_started: Rocket,
};

const EVENT_COLORS: Record<string, string> = {
  run_started: 'text-emerald-400',
  budget_configured: 'text-amber-400',
  execution_plan: 'text-blue-400',
  project_analyzed: 'text-cyan-400',
  stack_detected: 'text-purple-400',
  architecture_designed: 'text-cyan-400',
  file_plan_ready: 'text-indigo-400',
  qa_complete: 'text-orange-400',
};

const EVENT_BG: Record<string, string> = {
  run_started: 'border-emerald-500/20 bg-emerald-500/5',
  budget_configured: 'border-amber-500/20 bg-amber-500/5',
  execution_plan: 'border-blue-500/20 bg-blue-500/5',
  project_analyzed: 'border-cyan-500/20 bg-cyan-500/5',
  stack_detected: 'border-purple-500/20 bg-purple-500/5',
  architecture_designed: 'border-cyan-500/20 bg-cyan-500/5',
  file_plan_ready: 'border-indigo-500/20 bg-indigo-500/5',
  qa_complete: 'border-orange-500/20 bg-orange-500/5',
};

// ─── Atmos-Style Event Card ─────────────────────────────────────────────────

function EventCardBubble({ message }: { message: ChatMessage }) {
  const eventType = message.eventType || message.content;
  const IconComp = EVENT_ICONS[eventType] || Brain;
  const color = EVENT_COLORS[eventType] || 'text-blue-400';
  const bgColor = EVENT_BG[eventType] || 'border-blue-500/20 bg-blue-500/5';

  // Show real content if available, otherwise just the label
  const displayContent = message.content !== eventType ? message.content : eventType;
  const hasDetail = displayContent !== eventType;

  return (
    <div className="px-4 py-1">
      <div className={cn(
        "inline-flex items-center gap-2.5 rounded-xl border px-4 py-2.5 text-[13px] transition-all",
        "hover:scale-[1.01] hover:shadow-md",
        bgColor
      )}
        style={{ maxWidth: '85%' }}
      >
        <div className={cn("w-6 h-6 rounded-lg flex items-center justify-center shrink-0", bgColor)}>
          <IconComp size={14} className={color} />
        </div>
        <div className="flex flex-col min-w-0">
          <span className={cn("text-[11px] font-semibold", color)}>AI Team</span>
          {hasDetail ? (
            <span className="text-[13px] font-medium whitespace-pre-wrap" style={{ color: 'var(--ide-text)' }}>
              {displayContent}
            </span>
          ) : (
            <span className="font-mono text-[13px] font-medium" style={{ color: 'var(--ide-text)' }}>
              {eventType}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── AI Team Typing Indicator (Atmos-style) ─────────────────────────────────

function AITeamTypingIndicator() {
  return (
    <div className="px-4 py-1">
      <div className="inline-flex items-center gap-2.5 rounded-xl border border-blue-500/20 bg-blue-500/5 px-4 py-2.5 text-[13px]">
        <div className="w-6 h-6 rounded-lg flex items-center justify-center bg-blue-500/10">
          <Brain size={14} className="text-blue-400" />
        </div>
        <span className="text-[12px] font-semibold text-blue-400">AI Team</span>
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-[12px] font-medium text-emerald-400">typing</span>
      </div>
    </div>
  );
}



// ─── Message Bubble (user & general assistant) ──────────────────────────────

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  // Route to specialized bubbles
  if (!isUser && message.messageType === 'event_card') {
    return <EventCardBubble message={message} />;
  }
  if (!isUser && message.messageType === 'discussion') {
    return <DiscussionBubble message={message} />;
  }
  if (!isUser && (message.messageType === 'agent_status' || message.messageType === 'agent_result')) {
    return <AgentStatusBubble message={message} />;
  }

  const agentName = isUser ? 'You' : (message.agentName || 'AI Team');
  const IconComp = isUser ? User : getAgentIcon(message.agentIcon);
  const nameColor = isUser ? 'text-blue-400' : getAgentColor(message.agentName);

  return (
    <div className={cn("px-4 py-2", isUser ? "flex justify-end" : "flex justify-start")}>
      <div className={cn(
        "max-w-[85%] rounded-2xl px-4 py-3 text-[14px] leading-relaxed shadow-sm",
        isUser
          ? "bg-gradient-to-br from-blue-500/20 to-blue-600/20 border border-blue-500/30"
          : cn("border", getAgentBgColor(message.agentName) || "border border-var(--ide-border) bg-var(--ide-surface)")
      )}>
        <div className="flex items-center gap-2.5 mb-2">
          <div className={cn(
            "w-7 h-7 rounded-full flex items-center justify-center",
            isUser ? "bg-blue-500/20" : "bg-var(--ide-surface-hover)"
          )}>
            <IconComp size={14} className={nameColor} />
          </div>
          <span className={cn("text-[12px] font-semibold", nameColor)}>
            {agentName}
          </span>
          {message.isStreaming && (
            <div className="flex items-center gap-1.5 ml-auto">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
              <span className="text-[10px] text-blue-400">typing</span>
            </div>
          )}
        </div>
        <div className="whitespace-pre-wrap break-words pl-9" style={{ color: 'var(--ide-text)' }}>{message.content}</div>

        {/* File badges */}
        {message.files && message.files.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3 pt-3 pl-9" style={{ borderTop: '1px solid var(--ide-border-subtle)' }}>
            {message.files.map((f) => (
              <span
                key={f.path}
                className={cn(
                  "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium",
                  f.status === 'done'
                    ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                    : "bg-blue-500/15 text-blue-400 border border-blue-500/30"
                )}
              >
                <Code2 size={12} />
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
  const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Use individual selectors to avoid subscribing to the entire store
  const chatMessages = useIDEStore((s) => s.chatMessages);
  const addChatMessage = useIDEStore((s) => s.addChatMessage);
  const updateLastAssistantMessage = useIDEStore((s) => s.updateLastAssistantMessage);
  const appendToLastAssistantMessage = useIDEStore((s) => s.appendToLastAssistantMessage);

  const setAIStatus = useIDEStore((s) => s.setAIStatus);
  const setProject = useIDEStore((s) => s.setProject);
  const setWorkspaceMode = useIDEStore((s) => s.setWorkspaceMode);
  const workspaceMode = useIDEStore((s) => s.workspaceMode);
  const aiStatus = useIDEStore((s) => s.aiStatus);

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
    const ide = useIDEStore.getState;

    // Wire LiveWriter to flush characters into the store
    liveWriter.setFlushCallback((path, chunk) => {
      ide().appendToFile(path, chunk);
    });

    // Full chat messages from backend
    const offMsg = EventBus.on('AI_MESSAGE', (event) => {
      const { content, agentName, agentIcon, messageType, eventType, eventData } = event.payload as {
        content: string; agentName?: string; agentIcon?: string; messageType?: string;
        eventType?: string; eventData?: Record<string, any>;
      };
      if (content) {
        addChatMessage({
          role: 'assistant',
          content,
          isStreaming: false,
          agentName,
          agentIcon,
          messageType: (messageType as any) || 'chat',
          eventType,
          eventData,
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

    // Agent-to-agent discussions
    const offDiscussion = EventBus.on('AI_DISCUSSION', (event) => {
      const { from, to, icon, message } = event.payload as {
        from: string; to: string; icon: string; message: string;
      };
      if (message) {
        addChatMessage({
          role: 'assistant',
          content: message,
          isStreaming: false,
          agentName: from,
          agentIcon: icon,
          toAgent: to,
          messageType: 'discussion',
        });
      }
    });

    // ── AI starts writing a file: pre-create the tab ──
    const offFileWriting = EventBus.on('AI_FILE_WRITING', (event) => {
      const { path } = event.payload as { path: string };
      const state = ide();

      if (!state.openFiles.includes(path)) {
        state.createFile(path, '', true);
        state.setAIStatus('generating');
        state.setAICurrentFile(path);
      }
      state.setFileLiveWriting(path, true);
    });

    // ── Live file typing: AI streams file content in chunks ──
    // Deltas are buffered through LiveWriter for a smooth typewriter effect
    const offFileDelta = EventBus.on('AI_FILE_DELTA', (event) => {
      const { path, delta } = event.payload as { path: string; delta: string };
      const state = ide();

      // First delta for this file → create it and make it active
      if (!state.openFiles.includes(path)) {
        state.createFile(path, '', true);  // empty shell, content dripped via liveWriter
        state.setAIStatus('generating');
        state.setAICurrentFile(path);
      }

      if (delta) {
        liveWriter.push(path, delta);
      }
      state.setFileLiveWriting(path, true);
    });

    // ── File fully created (sent after all deltas, or as a single shot) ──
    const offFile = EventBus.on('FILE_CREATED', (event) => {
      const { path, content } = event.payload as { path: string; content: string };

      // Flush any remaining buffered characters for this file immediately
      liveWriter.flush(path);

      const state = ide();

      // Only overwrite with final content if it's non-empty.
      // During streaming, deltas build up content. If the final event has
      // content, use it (authoritative). If null/empty, keep the streamed version.
      const existingContent = state.fileContents[path] ?? '';
      const finalContent = content && content.length > 0 ? content : existingContent;
      state.createFile(path, finalContent, true);
      state.setFileLiveWriting(path, false);

      // Update chat message with file badge
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

    // ── File updated (hot-patch after error fixing) ──
    const offFileUpdated = EventBus.on('FILE_UPDATED', (event) => {
      const { path, content } = event.payload as { path: string; content: string };
      ide().updateFileContent(path, content);
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

    // Terminal output — route to terminal panel
    const offTerminal = EventBus.on('TERMINAL_OUTPUT', (event) => {
      const { text, type } = event.payload as { text: string; type: string };
      if (text) {
        ide().appendTerminalLine(text, (type as any) || 'stdout');
      }
    });

    // Pipeline done
    const offDone = EventBus.on('ATMOS_DONE', () => {
      // Flush any remaining buffered characters before closing out
      liveWriter.flush();

      setIsStreaming(false);
      setAIStatus('idle');

      const state = ide();

      // Stop live-writing on all files
      Object.keys(state.fileLiveWriting).forEach((p) => {
        if (state.fileLiveWriting[p]) {
          state.setFileLiveWriting(p, false);
        }
      });
      state.setAICurrentFile(null);

      // Mark last assistant message as not streaming
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
        // Derive project name from the first user message (the prompt)
        const allMsgs = useIDEStore.getState().chatMessages;
        const firstUserMsg = allMsgs.find((m) => m.role === 'user');
        const projectName = firstUserMsg
          ? firstUserMsg.content.slice(0, 120).trim() || 'My Project'
          : 'My Project';

        // Persist project to backend database
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/43ecb47a-12c1-41b6-b495-5c3e11c24556', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            location: 'AtomsChatPanel.tsx:project-create',
            message: 'create_project_request',
            data: {
              path: '/projects/',
              projectName,
              hasIdea: !!firstUserMsg?.content,
            },
            runId: 'pre-fix-1',
            hypothesisId: 'H1',
            timestamp: Date.now(),
          }),
        }).catch(() => { });
        // #endregion

        apiFetch<{ id: string; name: string }>('/projects/', {
          method: 'POST',
          body: JSON.stringify({ name: projectName, idea: firstUserMsg?.content || '' }),
        })
          .then((saved) => {
            setProject({ id: saved.id, name: saved.name });
          })
          .catch((err) => {
            // #region agent log
            fetch('http://127.0.0.1:7242/ingest/43ecb47a-12c1-41b6-b495-5c3e11c24556', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                location: 'AtomsChatPanel.tsx:project-create',
                message: 'create_project_error',
                data: {
                  path: '/projects/',
                  errorMessage: err instanceof Error ? err.message : String(err),
                },
                runId: 'pre-fix-1',
                hypothesisId: 'H2',
                timestamp: Date.now(),
              }),
            }).catch(() => { });
            // #endregion

            // Fallback to local-only project if not authenticated or API fails
            setProject({ id: 'generated', name: projectName });
          });

        setWorkspaceMode('project');
      }
    });

    return () => {
      liveWriter.reset();
      offMsg();
      offToken();
      offDiscussion();
      offFileWriting();
      offFileDelta();
      offFile();
      offFileUpdated();
      offError();
      offTerminal();
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

  // ─── Attachment Handlers ───────────────────────────────────────────────────────

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        const attachment: ChatAttachment = {
          id: Math.random().toString(36).substr(2, 9),
          name: file.name,
          type: file.type.startsWith('image/') ? 'image' :
            file.name.endsWith('.py') || file.name.endsWith('.js') ||
              file.name.endsWith('.ts') || file.name.endsWith('.tsx') ? 'code' : 'file',
          content,
          size: file.size,
          preview: file.type.startsWith('image/') ? content : undefined,
        };
        setAttachments(prev => [...prev, attachment]);
      };
      reader.readAsText(file);
    });

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const removeAttachment = useCallback((id: string) => {
    setAttachments(prev => prev.filter(att => att.id !== id));
  }, []);

  const isEmpty = chatMessages.length === 0 && workspaceMode === 'empty';

  return (
    <aside
      className={cn("flex flex-col h-full", embedded ? "w-full min-w-0" : "shrink-0")}
      style={embedded ? { background: "var(--ide-chat-bg)" } : {
        width: "480px", minWidth: 400, maxWidth: 600,
        background: "var(--ide-chat-bg)",
        borderLeft: '1px solid var(--ide-border)',
        boxShadow: '0 1px 2px rgba(0,0,0,0.04)'
      }}
    >
      {/* Top Navigation Bar */}
      <ChatTopBar />



      {/* Messages or Welcome */}
      <div className={cn(
        "flex-1 min-h-0",
        isEmpty ? "overflow-hidden" : "overflow-y-auto py-4 pb-28 space-y-1"
      )}>
        {isEmpty ? (
          <div className="flex flex-col h-full px-6">
            {/* Hero Section */}
            <div className="flex-1 flex flex-col items-center justify-center">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mb-6 border border-blue-500/30">
                <Sparkles size={28} className="text-blue-400" />
              </div>
              <h2 className="text-[26px] font-bold mb-3 tracking-tight text-center" style={{ color: 'var(--ide-text)' }}>
                What do you want to build?
              </h2>
              <p className="text-[14px] mb-8 text-center max-w-[360px] leading-relaxed" style={{ color: 'var(--ide-text-muted)' }}>
                Your AI team will collaborate in real-time to bring your vision to life.
              </p>

              {/* Agent Pills */}
              <div className="flex flex-wrap justify-center gap-2 mb-8">
                {[
                  { name: 'Team Lead', icon: Crown, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30' },
                  { name: 'PM', icon: ClipboardList, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/30' },
                  { name: 'Architect', icon: Layers, color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/30' },
                  { name: 'Engineer', icon: Code2, color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/30' },
                  { name: 'QA', icon: Shield, color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/30' },
                  { name: 'DevOps', icon: Rocket, color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/30' },
                ].map(({ name, icon: Icon, color, bg }) => (
                  <div key={name} className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[12px] font-medium", bg)}>
                    <Icon size={14} className={color} />
                    <span style={{ color: 'var(--ide-text-secondary)' }}>{name}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Example Prompts */}
            <div className="pb-6">
              <p className="text-[11px] font-semibold uppercase tracking-wider mb-3 text-center" style={{ color: 'var(--ide-text-muted)' }}>
                Try an example
              </p>
              <div className="grid grid-cols-2 gap-2">
                {EXAMPLE_PROMPTS.map(({ icon: Icon, title, prompt, color }) => (
                  <button
                    key={title}
                    onClick={() => {
                      const textarea = document.querySelector('textarea');
                      if (textarea) {
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
                        nativeInputValueSetter?.call(textarea, prompt);
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        textarea.focus();
                      }
                    }}
                    className="flex items-start gap-3 p-3 rounded-xl border text-left transition-all hover:scale-[1.02] hover:border-blue-500/50"
                    style={{
                      background: 'var(--ide-surface)',
                      borderColor: 'var(--ide-border)',
                    }}
                  >
                    <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center shrink-0", "bg-var(--ide-surface-hover)")}>
                      <Icon size={16} className={color} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-[13px] font-medium truncate" style={{ color: 'var(--ide-text)' }}>{title}</p>
                      <p className="text-[11px] line-clamp-2" style={{ color: 'var(--ide-text-muted)' }}>{prompt.slice(0, 60)}...</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {chatMessages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* AI Team • typing indicator (Atmos-style) */}
            {isStreaming && (
              <AITeamTypingIndicator />
            )}

            {/* Thinking indicator */}
            {isStreaming && atmosPhase === 'interpreting' && (
              <div className="flex items-center gap-2 px-5 text-[12px]" style={{ color: 'var(--ide-text-muted)' }}>
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

      {/* Input Area */}
      <div className="p-4 border-t bg-background shrink-0" style={{ borderColor: 'var(--ide-border)' }}>
        {/* Attachments Display */}
        {attachments.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {attachments.map((attachment) => (
              <div
                key={attachment.id}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border text-xs"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  borderColor: 'rgba(255, 255, 255, 0.1)',
                  color: 'rgba(255, 255, 255, 0.8)'
                }}
              >
                {attachment.type === 'image' ? (
                  <Paperclip size={14} className="text-blue-400" />
                ) : attachment.type === 'code' ? (
                  <Code2 size={14} className="text-green-400" />
                ) : (
                  <Upload size={14} className="text-gray-400" />
                )}
                <span className="truncate max-w-[140px] font-medium">{attachment.name}</span>
                <button
                  className="p-0.5 rounded transition-colors"
                  style={{ color: 'var(--ide-text-muted)' }}
                  onClick={() => removeAttachment(attachment.id)}
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex flex-col gap-2 p-3 rounded-xl border border-input bg-zinc-900/50 focus-within:border-primary transition-colors">
          <div className="flex items-start gap-2">
            {/* Attachment Button */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileUpload}
              className="hidden"
              accept=".txt,.py,.js,.ts,.tsx,.jsx,.md,.json,.yaml,.yml,.html,.css,.scss,.png,.jpg,.jpeg,.gif,.svg,.pdf"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-1.5 rounded-lg hover:bg-zinc-800 text-zinc-400 transition-colors"
              title="Add context (files, images)"
            >
              <Plus size={16} />
            </button>

            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="What do you want to build?"
              className="w-full bg-transparent border-none outline-none resize-none text-[14px] leading-relaxed py-1 no-scrollbar"
              disabled={isStreaming}
            />

            {/* Send/Stop Button */}
            <div className="shrink-0 mt-1">
              {isStreaming ? (
                <button
                  onClick={handleStop}
                  className="p-2 rounded-lg flex items-center gap-1.5 text-[12px] font-medium transition-all hover:bg-red-500/20"
                  style={{ color: '#ef4444' }}
                >
                  <RotateCcw size={16} />
                </button>
              ) : (
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isStreaming}
                  className={cn(
                    "p-1.5 rounded-lg transition-all",
                    input.trim() && !isStreaming
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                      : "bg-zinc-800 text-zinc-500 opacity-50 cursor-not-allowed"
                  )}
                >
                  <ArrowRight size={16} />
                </button>
              )}
            </div>
          </div>

          {/* Keyboard hint */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-zinc-800/50 border border-zinc-700/50 text-[10px] text-zinc-400">
              <span>Enter to send</span>
              <span className="w-1 h-1 rounded-full bg-zinc-600" />
              <span>Shift+Enter new line</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
