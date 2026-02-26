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

import { useState, useCallback, useRef, useEffect, useMemo, Fragment, memo, Component } from "react";
import {
  Loader2,
  RotateCcw,
  Crown, ClipboardList, Layers, Code2, Shield, Rocket,
  Brain, ArrowRight, CheckCircle2, Activity, AlertCircle,
  Sparkles, Zap, Globe, Database, MessageSquare,
  Play, Settings, FileCode, Search,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useIDEStore, type ChatMessage } from "@/stores/ide-store";
import { EventBus, useEventBus } from "@/lib/event-bus";
import { useAtmosStore, type AtmosPhase } from "@/lib/atmos-state";
import { runNimIntent } from "@/lib/nim-ws";
import { InputArea } from "@/components/chat/InputArea";
import {
  type ChatAttachment,
  MAX_FILE_SIZE,
  MAX_TOTAL_SIZE,
  ALLOWED_MIME_TYPES,
  validateAttachmentsForSend,
} from "@/components/chat/attachment";
import { ChatTopBar } from "@/components/ChatTopBar";
import { liveWriter } from "@/lib/live-writer";
import { apiFetch } from "@/lib/api";
import { useStreamStore } from "@/streaming/stream-store";
import { AgentPresenceBar } from "@/components/streaming/AgentPresenceBar";
import { FileBatchCard } from "@/components/streaming/FileBatchCard";
import { ModeToggle } from "@/components/streaming/ModeToggle";
import { PhaseBlock } from "@/components/streaming/PhaseBlock";
import { CompletionCard } from "@/components/streaming/CompletionCard";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import Prism from "prismjs";
import "prismjs/components/prism-typescript";
import "prismjs/components/prism-javascript";
import "prismjs/components/prism-python";
import "prismjs/components/prism-bash";
import "prismjs/components/prism-json";
import "prismjs/components/prism-css";
import "prismjs/components/prism-jsx";
import "prismjs/components/prism-tsx";
import "prismjs/components/prism-sql";
import "prismjs/components/prism-yaml";
import "prismjs/components/prism-markdown";

// ─── Error Boundary ───────────────────────────────────────────────────────────
// Prevents a single bad message from crashing the entire chat panel.

interface EBState { hasError: boolean }
class MessageErrorBoundary extends Component<{ children: React.ReactNode }, EBState> {
  state: EBState = { hasError: false };
  static getDerivedStateFromError(): EBState { return { hasError: true }; }
  componentDidCatch(err: Error, info: React.ErrorInfo) {
    console.error('[MessageBubble] Render error:', err, info.componentStack);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '8px 20px', borderBottom: '1px solid var(--border-subtle)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span style={{ fontSize: 12, color: 'rgba(248,113,113,0.7)', fontFamily: 'var(--font-ui)' }}>
            ⚠ Message failed to render.
          </span>
        </div>
      );
    }
    return this.props.children;
  }
}

// ─── Grouped EventBus Subscription Hook ──────────────────────────────────────
// Registers and unregisters multiple EventBus listeners as one unit.
// Prevents the 11-listener effect from becoming unmaintainable.

type EventHandler = (event: import('@/lib/event-bus').AtmosEvent) => void;
type EventSubscription = [import('@/lib/event-bus').AtmosEventType, EventHandler];

function useEventBusSubscriptions(subscriptions: EventSubscription[]): void {
  // Keep subscriptions stable via ref so effect needn't re-run on every render
  const subsRef = useRef(subscriptions);
  subsRef.current = subscriptions;

  useEffect(() => {
    const offs = subsRef.current.map(([type, handler]) =>
      EventBus.on(type, handler)
    );
    return () => offs.forEach(off => off());
    // Empty deps: subscriptions are stable within a session
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}

// ─── Markdown Renderer (lightweight fallback) ───────────────────────────────

function escHtml(t: string): string {
  return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderMarkdown(text: string): string {
  if (!text) return '';
  return text
    .replace(/```(\w*)\n([\s\S]*?)```/g, (_: string, lang: string, code: string) =>
      `<pre class="md-code-block"><code class="lang-${lang}">${escHtml(code.trim())}</code></pre>`)
    .replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, (m: string) => `<ul>${m}</ul>`)
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[hupol]|<pre)(.+)$/gm, (m: string) => m || '');
}

// ─── Rich Markdown Component (react-markdown + PrismJS) ─────────────────────

const EXT_TO_LANG: Record<string, string> = {
  ts: 'typescript', tsx: 'tsx', js: 'javascript', jsx: 'jsx',
  py: 'python', sh: 'bash', bash: 'bash', json: 'json',
  css: 'css', scss: 'css', sql: 'sql', yaml: 'yaml', yml: 'yaml',
  md: 'markdown', html: 'markup', xml: 'markup',
};

function detectLanguage(lang?: string | null): string {
  if (!lang) return 'markup';
  const lower = lang.toLowerCase();
  return EXT_TO_LANG[lower] ?? lower;
}

/** Syntax-highlighted code block used inside ReactMarkdown */
function PrismCodeBlock({ className, children, ...props }: React.HTMLAttributes<HTMLElement> & { children?: React.ReactNode }) {
  const match = /language-(\w+)/.exec(className || '');
  const lang = detectLanguage(match?.[1]);
  const code = String(children).replace(/\n$/, '');

  if (!match) {
    // Inline code
    return <code className="md-inline-code" {...props}>{children}</code>;
  }

  // Fenced code block with syntax highlighting
  let html = code;
  try {
    const grammar = Prism.languages[lang];
    if (grammar) {
      html = Prism.highlight(code, grammar, lang);
    }
  } catch {
    // fallback to plain text
  }

  return (
    <pre className="md-code-block prism-highlighted">
      <div className="md-code-lang-badge">{match[1]}</div>
      <code
        className={`language-${lang}`}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </pre>
  );
}

/** Rich markdown renderer — sanitized, with GFM + syntax highlighting */
const MarkdownContent = memo(function MarkdownContent({ text }: { text: string }) {
  if (!text) return null;
  return (
    <div className="md-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          code: PrismCodeBlock as any,
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
});

// ─── Copy Button ─────────────────────────────────────────────────────────────

function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        navigator.clipboard.writeText(text).catch(() => {});
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      style={{
        background: copied ? 'rgba(52,211,153,0.10)' : 'rgba(255,255,255,0.04)',
        border: `1px solid ${copied ? 'rgba(52,211,153,0.30)' : 'rgba(255,255,255,0.08)'}`,
        borderRadius: 6,
        padding: '3px 10px',
        color: copied ? '#34d399' : 'rgba(255,255,255,0.38)',
        fontSize: 11,
        cursor: 'pointer',
        transition: 'all 0.2s',
        fontFamily: 'var(--font-ui)',
      }}
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
}

// ─── Rich Agent Config ───────────────────────────────────────────────────────

interface AgentCfg {
  label: string; role: string; avatar: string;
  color: string; glow: string; border: string; borderActive: string; dim: string;
}

const AGENT_CFG_RICH: Record<string, AgentCfg> = {
  'Team Leader':        { label: 'Team Leader',        role: 'Orchestrator',   avatar: 'TL', color: '#e8a245', glow: 'rgba(232,162,69,0.20)',  border: 'rgba(232,162,69,0.20)',  borderActive: 'rgba(232,162,69,0.55)',  dim: 'rgba(232,162,69,0.07)' },
  'Database Engineer':  { label: 'Database Engineer',  role: 'Data & Schema',  avatar: 'DB', color: '#60a5fa', glow: 'rgba(96,165,250,0.18)',   border: 'rgba(96,165,250,0.20)',   borderActive: 'rgba(96,165,250,0.55)',  dim: 'rgba(96,165,250,0.07)' },
  'Backend Engineer':   { label: 'Backend Engineer',   role: 'API & Logic',    avatar: 'BE', color: '#34d399', glow: 'rgba(52,211,153,0.18)',   border: 'rgba(52,211,153,0.20)',   borderActive: 'rgba(52,211,153,0.55)',  dim: 'rgba(52,211,153,0.07)' },
  'Frontend Engineer':  { label: 'Frontend Engineer',  role: 'UI & UX',        avatar: 'FE', color: '#38bdf8', glow: 'rgba(56,189,248,0.18)',   border: 'rgba(56,189,248,0.20)',   borderActive: 'rgba(56,189,248,0.55)',  dim: 'rgba(56,189,248,0.07)' },
  'QA Engineer':        { label: 'QA Engineer',        role: 'Quality',        avatar: 'QA', color: '#fb923c', glow: 'rgba(251,146,60,0.18)',   border: 'rgba(251,146,60,0.20)',   borderActive: 'rgba(251,146,60,0.55)',  dim: 'rgba(251,146,60,0.07)' },
  // Legacy names kept for backwards compat
  'Engineer':           { label: 'Engineer',           role: 'Developer',      avatar: 'EN', color: '#34d399', glow: 'rgba(52,211,153,0.18)',   border: 'rgba(52,211,153,0.20)',   borderActive: 'rgba(52,211,153,0.55)',  dim: 'rgba(52,211,153,0.07)' },
  'Orchestrator':       { label: 'Orchestrator',       role: 'System',         avatar: 'OR', color: '#94a3b8', glow: 'rgba(148,163,184,0.12)',  border: 'rgba(148,163,184,0.15)',  borderActive: 'rgba(148,163,184,0.35)', dim: 'rgba(148,163,184,0.05)' },
};
const DEFAULT_CFG: AgentCfg = {
  label: 'Team Lead', role: 'Orchestrator', avatar: 'TL',
  color: '#818cf8', glow: 'rgba(129,140,248,0.18)', border: 'rgba(129,140,248,0.20)', borderActive: 'rgba(129,140,248,0.55)', dim: 'rgba(129,140,248,0.07)',
};

function getAgentCfg(name?: string): AgentCfg {
  if (!name) return DEFAULT_CFG;
  return AGENT_CFG_RICH[name] ?? DEFAULT_CFG;
}

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

// ─── Smooth token buffer (~30 fps drip for thinking blocks) ─────────────────
// Prevents burst re-renders when the backend sends tokens in rapid bursts.

class TokenDripBuffer {
  private queue: string[] = [];
  private timerId: ReturnType<typeof setInterval> | null = null;
  private flush: (batch: string) => void;

  constructor(flush: (batch: string) => void) {
    this.flush = flush;
  }

  push(token: string) {
    this.queue.push(token);
    this.start();
  }

  private start() {
    if (this.timerId !== null) return;
    this.timerId = setInterval(() => {
      if (this.queue.length === 0) { this.stop(); return; }
      // Release up to 4 chars per frame (~30fps = 33ms) — smooth but not laggy
      this.flush(this.queue.splice(0, 4).join(''));
    }, 33);
  }

  private stop() {
    if (this.timerId !== null) { clearInterval(this.timerId); this.timerId = null; }
  }

  drainAll(flush: (batch: string) => void) {
    this.stop();
    if (this.queue.length > 0) { flush(this.queue.splice(0).join('')); }
  }

  reset() {
    this.stop();
    this.queue = [];
  }
}

// ─── Narrative Drip — streams seed text char-by-char into PhaseBlock ─────────
// When an agent starts, we drip the narrative text so it appears to type in
// live. If real backend tokens arrive, we cancel the drip and switch to those.

class NarrativeDrip {
  private chars: string[] = [];
  private timerId: ReturnType<typeof setInterval> | null = null;

  /** Start dripping `text` into `onChunk` at ~200 chars/sec (4 chars / 20ms). */
  start(text: string, onChunk: (chunk: string) => void) {
    this.stop();
    this.chars = text.split('');
    this.timerId = setInterval(() => {
      if (this.chars.length === 0) { this.stop(); return; }
      // 4 chars per tick at 20ms ≈ 200 chars/sec — fast and snappy
      onChunk(this.chars.splice(0, 4).join(''));
    }, 20);
  }

  /** Cancel mid-drip (real tokens have arrived). */
  stop() {
    if (this.timerId !== null) { clearInterval(this.timerId); this.timerId = null; }
    this.chars = [];
  }

  reset() { this.stop(); }
}

// ─── Message Pacing Queue (cinematic rhythm ~300ms between narrative events) ──
// Only delays event_card + discussion messages. Thinking / code = immediate.

class MessageQueue {
  private queue: Array<() => void> = [];
  private timer: ReturnType<typeof setTimeout> | null = null;
  private delay = 50; // ms between messages — fast enough to feel live

  enqueue(fn: () => void) {
    this.queue.push(fn);
    this.scheduleNext();
  }

  private scheduleNext() {
    if (this.timer !== null) return;
    this.timer = setTimeout(() => {
      this.timer = null;
      const fn = this.queue.shift();
      if (fn) {
        fn();
        if (this.queue.length > 0) this.scheduleNext();
      }
    }, this.delay);
  }

  flush() {
    if (this.timer !== null) { clearTimeout(this.timer); this.timer = null; }
    this.queue.forEach(fn => fn());
    this.queue = [];
  }

  reset() {
    if (this.timer !== null) { clearTimeout(this.timer); this.timer = null; }
    this.queue = [];
  }
}


// ─── Visual Primitives ───────────────────────────────────────────────────────

/** Blinking block-cursor, used inside streaming text blocks */
function BlinkCursor({ on, color = '#34d399' }: { on: boolean; color?: string }) {
  const [v, setV] = useState(true);
  useEffect(() => {
    if (!on) return;
    const t = setInterval(() => setV(x => !x), 530);
    return () => clearInterval(t);
  }, [on]);
  if (!on) return null;
  return (
    <span
      aria-hidden
      style={{ opacity: v ? 1 : 0, color, fontWeight: 700, fontSize: '1em', userSelect: 'none', transition: 'opacity 80ms' }}
    >
      ▍
    </span>
  );
}

/** Glowing pulsing dot — live activity indicator */
function PulsingDot({ color = '#34d399', size = 6 }: { color?: string; size?: number }) {
  return (
    <span
      style={{
        display: 'inline-block',
        width: size,
        height: size,
        minWidth: size,
        borderRadius: '50%',
        background: color,
        boxShadow: `0 0 ${size + 2}px ${color}`,
        animation: 'pulse 1.3s ease infinite',
        flexShrink: 0,
      }}
    />
  );
}

/** 2-letter agent avatar box with per-agent glow */
function AgentAvatarBox({ name, isStreaming }: { name?: string; isStreaming?: boolean }) {
  const cfg = getAgentCfg(name);
  const size = 36;
  return (
    <div
      style={{
        width: size,
        height: size,
        minWidth: size,
        borderRadius: Math.round(size * 0.28),
        background: `linear-gradient(135deg, ${cfg.color}22, ${cfg.color}0a)`,
        border: `1.5px solid ${isStreaming ? cfg.borderActive : cfg.border}`,
        boxShadow: isStreaming ? `0 0 16px ${cfg.glow}` : 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: Math.round(size * 0.30),
        fontWeight: 700,
        color: cfg.color,
        fontFamily: 'var(--font-mono)',
        letterSpacing: '0.04em',
        transition: 'border-color 0.3s ease, box-shadow 0.3s ease',
        userSelect: 'none',
        flexShrink: 0,
      }}
    >
      {cfg.avatar}
    </div>
  );
}

/** Reusable agent-message row: avatar left, header + content right */
function AgentRow({
  name, isStreaming, streamLabel, children,
}: {
  name?: string; isStreaming?: boolean; streamLabel?: string;
  children: React.ReactNode;
}) {
  const cfg = getAgentCfg(name);
  return (
    <div style={{ display: 'flex', gap: 13, padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', animation: 'fadeSlideUp 0.35s ease' }}>
      <div style={{ paddingTop: 2 }}>
        <AgentAvatarBox name={name} isStreaming={isStreaming} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 10 }}>
          <span style={{
            fontSize: 14,
            fontWeight: 700,
            color: cfg.color,
            fontFamily: 'var(--font-ui)',
            letterSpacing: '0.01em',
          }}>
            {cfg.label}
          </span>
          <span className="agent-role-badge">
            {cfg.role}
          </span>
          {isStreaming && streamLabel && (
            <div style={{
              marginLeft: 'auto',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 11,
              fontWeight: 600,
              color: cfg.color,
              fontFamily: 'var(--font-ui)',
            }}>
              <PulsingDot color={cfg.color} size={5} />
              {streamLabel}
            </div>
          )}
        </div>
        {children}
      </div>
    </div>
  );
}

// ─── Discussion Bubble (Agent-to-Agent reply) ────────────────────────────────
// Clean Slack-style message: avatar + name + role + optional recipient pill.
// No collapsing. Text always full opacity. Copy button on hover.

function DiscussionBubble({ message }: { message: ChatMessage }) {
  const cfg = getAgentCfg(message.agentName);
  const toCfg = getAgentCfg(message.toAgent);
  const isActive = message.isStreaming === true;

  return (
    <div className="agent-msg-row" style={{
      display: 'flex',
      gap: 13,
      padding: '14px 20px',
      borderBottom: '1px solid var(--border-subtle)',
      animation: 'fadeSlideUp 0.3s ease both',
    }}>
      {/* Avatar */}
      <div style={{ paddingTop: 2, flexShrink: 0 }}>
        <AgentAvatarBox name={message.agentName} isStreaming={isActive} />
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Header: name + role badge + optional recipient pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 7,
          marginBottom: 8,
          flexWrap: 'wrap',
        }}>
          <span style={{ fontSize: 13.5, fontWeight: 700, color: cfg.color, fontFamily: 'var(--font-ui)', letterSpacing: '0.01em' }}>
            {cfg.label}
          </span>
          <span className="agent-role-badge">{cfg.role}</span>

          {message.toAgent && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: '2px 8px',
              borderRadius: 20,
              background: `${toCfg.color}10`,
              border: `1px solid ${toCfg.color}28`,
            }}>
              <ArrowRight size={9} style={{ color: toCfg.color, flexShrink: 0 }} />
              <span style={{ fontSize: 10.5, fontWeight: 600, color: toCfg.color, fontFamily: 'var(--font-ui)' }}>
                {message.toAgent}
              </span>
            </div>
          )}
        </div>

        {/* Message body */}
        <div style={{
          fontSize: 13.5,
          lineHeight: 1.72,
          color: 'var(--text-primary)',
          fontFamily: 'var(--font-ui)',
          wordBreak: 'break-word',
          borderLeft: `2px solid ${cfg.color}45`,
          paddingLeft: 12,
        }}>
          {isActive ? (
            <span style={{ whiteSpace: 'pre-wrap' }}>
              {message.content}
              <BlinkCursor on color={cfg.color} />
            </span>
          ) : (
            <MarkdownContent text={message.content} />
          )}
        </div>

        {/* Hover-reveal copy button */}
        {!isActive && message.content && (
          <div className="msg-actions" style={{ display: 'flex', gap: 6, marginTop: 7, paddingLeft: 14 }}>
            <CopyBtn text={message.content} />
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Agent Status Bubble ────────────────────────────────────────────────────
// agent_status → slim centered timeline pill (non-intrusive activity marker)
// agent_result → compact green result line with check icon

function agentStreamVerb(agentName?: string): string {
  if (!agentName) return 'working';
  if (agentName === 'Team Leader') return 'coordinating';
  if (agentName === 'Database Engineer') return 'designing schema';
  if (agentName === 'Backend Engineer') return 'coding';
  if (agentName === 'Frontend Engineer') return 'building UI';
  if (agentName === 'QA Engineer') return 'reviewing';
  if (agentName === 'Engineer' || agentName === 'Planner') return 'coding';
  if (agentName === 'DevOps') return 'deploying';
  if (agentName === 'Architect') return 'designing';
  if (agentName === 'Product Manager' || agentName === 'Product Mgr') return 'planning';
  return 'working';
}

function AgentStatusBubble({ message }: { message: ChatMessage }) {
  const isResult = message.messageType === 'agent_result';
  const cfg = getAgentCfg(message.agentName);

  if (!isResult) {
    // Slim timeline-divider pill: "· Backend Engineer · coding ·"
    const verb = agentStreamVerb(message.agentName);
    return (
      <div className="flex items-center gap-3 px-5 py-1.5">
        <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.04)' }} />
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          fontSize: 11, fontFamily: 'var(--font-ui)', color: cfg.color,
          opacity: 0.7, whiteSpace: 'nowrap',
        }}>
          <PulsingDot color={cfg.color} size={4} />
          <span style={{ fontWeight: 600 }}>{cfg.label}</span>
          <span style={{ color: 'rgba(255,255,255,0.28)' }}>·</span>
          <span>{verb}</span>
        </div>
        <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.04)' }} />
      </div>
    );
  }

  // Agent result — compact inline row with check + text
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 10,
      padding: '8px 20px',
      borderBottom: '1px solid var(--border-subtle)',
      animation: 'fadeSlideUp 0.25s ease both',
    }}>
      <div style={{ paddingTop: 3, flexShrink: 0 }}>
        <CheckCircle2 size={13} style={{ color: '#34d399' }} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: cfg.color, fontFamily: 'var(--font-ui)' }}>
            {cfg.label}
          </span>
          <span style={{ fontSize: 10, color: '#34d399', fontWeight: 600, fontFamily: 'var(--font-ui)' }}>
            completed
          </span>
        </div>
        {message.content && (
          <div style={{
            fontSize: 12.5, lineHeight: 1.65,
            color: 'rgba(255,255,255,0.62)',
            fontFamily: 'var(--font-ui)',
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          }}>
            {message.content}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Event Card Icons ────────────────────────────────────────────────────────

const EVENT_ICONS: Record<string, typeof Brain> = {
  run_started: Play,
  budget_configured: Settings,
  model_configured: Brain,
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
  model_configured: 'text-sky-400',
  execution_plan: 'text-blue-400',
  project_analyzed: 'text-cyan-400',
  stack_detected: 'text-purple-400',
  architecture_designed: 'text-cyan-400',
  file_plan_ready: 'text-indigo-400',
  qa_complete: 'text-orange-400',
};


// ─── System Event Divider (slim centered timeline pill — no card, no "AI" label)
// Looks like Linear/Claude.ai timeline markers.

function EventCardBubble({ message }: { message: ChatMessage }) {
  const eventType = message.eventType || message.content;
  const IconComp = EVENT_ICONS[eventType] || Brain;
  const color = EVENT_COLORS[eventType] || 'text-slate-400';

  const displayContent = (message.content && message.content !== eventType)
    ? message.content
    : eventType.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="flex items-center gap-3 px-5 py-2">
      <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.05)' }} />
      <div className={cn('flex items-center gap-1.5 text-[10.5px] font-medium select-none whitespace-nowrap', color)}>
        <IconComp size={10} className="shrink-0 opacity-70" />
        <span className="opacity-80">{displayContent}</span>
      </div>
      <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.05)' }} />
    </div>
  );
}

// ─── Agent Speech Bubble ─────────────────────────────────────────────────────
// Claude/ChatGPT-style: avatar + name + role, text always full opacity,
// blinking cursor while streaming, markdown when done, hover-reveal actions.

function AgentSpeechBubble({ message, isLast, onRegen }: { message: ChatMessage; isLast?: boolean; onRegen?: () => void }) {
  const cfg = getAgentCfg(message.agentName);
  const isActive = message.isStreaming === true;

  return (
    <div
      className="agent-msg-row"
      style={{
        display: 'flex',
        gap: 13,
        padding: '15px 20px',
        borderBottom: '1px solid var(--border-subtle)',
        animation: 'fadeSlideUp 0.32s ease both',
      }}
    >
      {/* Avatar — glows while streaming */}
      <div style={{ paddingTop: 2, flexShrink: 0 }}>
        <AgentAvatarBox name={message.agentName} isStreaming={isActive} />
      </div>

      {/* Content column */}
      <div style={{ flex: 1, minWidth: 0 }}>

        {/* Header: name + role badge + subtle live dot (no text label) */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 9 }}>
          <span style={{
            fontSize: 13.5,
            fontWeight: 700,
            color: cfg.color,
            fontFamily: 'var(--font-ui)',
            letterSpacing: '0.01em',
          }}>
            {cfg.label}
          </span>
          <span className="agent-role-badge">{cfg.role}</span>
          {isActive && <PulsingDot color={cfg.color} size={5} />}
        </div>

        {/* Body: full opacity always, cursor while streaming, markdown when done */}
        <div
          className={!isActive && message.content ? 'agent-speech-done' : ''}
          style={{
            fontSize: 13.5,
            lineHeight: 1.75,
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-ui)',
            wordBreak: 'break-word',
            borderLeft: `2px solid ${isActive ? cfg.color : 'rgba(255,255,255,0.07)'}`,
            paddingLeft: 12,
            transition: 'border-color 0.4s ease',
          }}
        >
          {isActive ? (
            <span style={{ whiteSpace: 'pre-wrap' }}>
              {message.content || ' '}
              <BlinkCursor on color={cfg.color} />
            </span>
          ) : (
            <MarkdownContent text={message.content || ''} />
          )}
        </div>

        {/* Hover-reveal: copy + optional regenerate */}
        {!isActive && message.content && (
          <div className="msg-actions" style={{ display: 'flex', gap: 6, marginTop: 8, paddingLeft: 14, alignItems: 'center' }}>
            <CopyBtn text={message.content} />
            {isLast && onRegen && (
              <button
                type="button"
                onClick={onRegen}
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: 6,
                  padding: '3px 10px',
                  color: 'rgba(255,255,255,0.38)',
                  fontSize: 11,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-ui)',
                  transition: 'color 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.72)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.38)'; }}
              >
                ↺ Regenerate
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Pipeline Stage Bar (Analyzing → Writing Code → Building → Running → Live) ─

const PIPELINE_STAGES: Array<{ phase: AtmosPhase; label: string; icon: typeof Brain }> = [
  { phase: 'interpreting', label: 'Analyzing', icon: Brain },
  { phase: 'generating', label: 'Writing Code', icon: Code2 },
  { phase: 'building', label: 'Building', icon: Settings },
  { phase: 'running', label: 'Running', icon: Rocket },
  { phase: 'live', label: 'Live', icon: Globe },
];

const PHASE_STAGE_INDEX: Partial<Record<AtmosPhase, number>> = {
  interpreting: 0,
  generating: 1,
  building: 2,
  running: 3,
  live: 4,
  error_fixing: -1, // special
};

function PipelineBar({ phase }: { phase: AtmosPhase }) {
  if (phase === 'idle') return null;

  const activeIdx = PHASE_STAGE_INDEX[phase] ?? -1;
  const isError = phase === 'error_fixing';
  const activeColor = isError ? '#f87171' : '#818cf8';
  const activeBg = isError ? 'rgba(248,113,113,0.12)' : 'rgba(99,102,241,0.15)';
  const activeBorder = isError ? 'rgba(248,113,113,0.38)' : 'rgba(129,140,248,0.40)';

  return (
    <div className="pipeline-rail">
      {PIPELINE_STAGES.map((stage, i) => {
        const isDone = i < activeIdx;
        const isActive = i === activeIdx;

        return (
          <Fragment key={stage.phase}>
            <div
              className={`pipeline-stage${isActive ? ' active' : isDone ? ' done' : ' upcoming'}`}
              style={isActive ? { background: activeBg, borderColor: activeBorder, color: activeColor } : {}}
            >
              {isDone && <span style={{ fontSize: 9, color: 'var(--success)' }}>✓</span>}
              {isActive && <PulsingDot color={activeColor} size={5} />}
              {!isDone && !isActive && (
                <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'rgba(255,255,255,0.15)', display: 'inline-block', flexShrink: 0 }} />
              )}
              <span style={isActive ? { fontWeight: 700 } : {}}>{stage.label}</span>
            </div>

            {i < PIPELINE_STAGES.length - 1 && (
              <div
                className="pipeline-connector"
                style={{ background: isDone ? 'rgba(52,211,153,0.25)' : 'var(--border-subtle)' }}
              />
            )}
          </Fragment>
        );
      })}
    </div>
  );
}

// ─── Live Phase Status Bar ───────────────────────────────────────────────────

function LivePhaseBar({ phase }: { phase: AtmosPhase }) {
  type Cfg = { icon: typeof Brain; color: string; dot: string; text: string; spin?: true };
  const configs: Partial<Record<AtmosPhase, Cfg>> = {
    interpreting: { icon: Brain, color: 'text-indigo-400', dot: 'bg-indigo-400', text: 'Analyzing your request...' },
    generating: { icon: Code2, color: 'text-green-400', dot: 'bg-green-400', text: 'Writing code...' },
    building: { icon: Loader2, color: 'text-amber-400', dot: 'bg-amber-400', text: 'Installing dependencies...', spin: true },
    running: { icon: Loader2, color: 'text-emerald-400', dot: 'bg-emerald-400', text: 'Starting dev server...', spin: true },
    error_fixing: { icon: RotateCcw, color: 'text-red-400', dot: 'bg-red-400', text: 'Auto-fixing issue...' },
  };
  const cfg = configs[phase];
  if (!cfg) return null;
  const IconComp = cfg.icon;
  return (
    <div className="flex items-center gap-2 px-5 py-2 text-[12px]">
      <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse shrink-0", cfg.dot)} />
      <IconComp size={12} className={cn(cfg.color, cfg.spin ? "animate-spin" : "animate-pulse")} />
      <span className={cfg.color}>{cfg.text}</span>
    </div>
  );
}


// ─── Duration Formatter ──────────────────────────────────────────────────────

function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
}

// ─── Code Block (macOS-style with traffic lights + copy) ─────────────────────

function CodeBlock({ message }: { message: ChatMessage }) {
  const [copied, setCopied] = useState(false);
  const cfg = getAgentCfg(message.agentName);
  const filename = message.eventData?.file || message.eventData?.filename || 'code';
  const isActive = message.isStreaming === true;

  // Detect language from file extension
  const ext = String(filename).split('.').pop()?.toLowerCase() || '';
  const lang = detectLanguage(ext);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(message.content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [message.content]);

  // Syntax-highlight the code content (only when not actively streaming for perf)
  const highlightedHtml = useMemo(() => {
    if (isActive || !message.content) return null;
    try {
      const grammar = Prism.languages[lang];
      if (grammar) {
        return Prism.highlight(message.content, grammar, lang);
      }
    } catch {
      // fallback
    }
    return null;
  }, [message.content, lang, isActive]);

  return (
    <div className="code-block-container" style={{ border: `1px solid ${isActive ? cfg.borderActive : 'rgba(255,255,255,0.08)'}`, transition: 'border-color 0.3s ease' }}>
      {/* Header with traffic lights + filename */}
      <div className="code-header">
        <div className="traffic-lights">
          <span className="traffic-light" style={{ background: '#ff5f56' }} />
          <span className="traffic-light" style={{ background: '#febc2e' }} />
          <span className="traffic-light" style={{ background: '#27c93f' }} />
        </div>
        <span style={{ color: cfg.color, fontFamily: 'var(--font-mono)', fontSize: 11.5, fontWeight: 600, letterSpacing: '0.02em' }}>
          {filename}
        </span>
        {ext && (
          <span style={{ fontSize: 10, color: 'var(--text-dim)', fontFamily: 'var(--font-ui)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {ext}
          </span>
        )}
        {isActive && (
          <span style={{ color: `${cfg.color}80`, fontSize: 10, fontFamily: 'var(--font-ui)', display: 'flex', alignItems: 'center', gap: 5 }}>
            <PulsingDot color={cfg.color} size={4} />
            writing…
          </span>
        )}
        <button
          type="button"
          className={`copy-btn${copied ? ' copy-btn-copied' : ''}`}
          onClick={handleCopy}
          style={{ marginLeft: 'auto' }}
        >
          {copied ? '✓ Copied' : 'Copy'}
        </button>
      </div>

      {/* Code body — syntax highlighted when done, plain text while streaming */}
      <div className={`code-body${highlightedHtml ? ' prism-highlighted' : ''}`}>
        {highlightedHtml ? (
          <code
            className={`language-${lang}`}
            dangerouslySetInnerHTML={{ __html: highlightedHtml }}
          />
        ) : (
          <>
            {message.content}
            <BlinkCursor on={isActive} color={cfg.color} />
          </>
        )}
      </div>
    </div>
  );
}

// ─── Status Pill (centered completion signal) ────────────────────────────────

function StatusPill({ message }: { message: ChatMessage }) {
  const durationMs = message.eventData?.duration;
  const agentName = message.agentName || 'Agent';
  const humanDuration = durationMs ? formatDuration(durationMs) : '';

  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '6px 0' }}>
      <div className="status-pill">
        <span style={{ color: 'var(--success)', fontSize: 11 }}>✓</span>
        <span>{agentName} finished</span>
        {humanDuration && (
          <>
            <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>·</span>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--success)', fontSize: 11.5 }}>
              {humanDuration}
            </span>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Error Block (red tinted box with retry) ─────────────────────────────────

function ErrorBlock({ message, onRetry }: { message: ChatMessage; onRetry?: () => void }) {
  return (
    <div className="error-block">
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <span style={{ fontSize: 15, color: 'var(--error)', marginTop: 1, flexShrink: 0 }}>⚠</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--error)', fontFamily: 'var(--font-ui)', marginBottom: 4 }}>
            {message.agentName ? `${message.agentName} failed` : 'Agent failed'}
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'rgba(255,255,255,0.60)', fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap' }}>
            {message.content.replace(/^⚠️?\s*/, '')}
          </div>
          {onRetry && (
            <button type="button" className="error-retry-btn" onClick={onRetry}>
              <RotateCcw size={11} /> Retry agent
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Active Agent Indicator Bar (bottom live indicator) ──────────────────────

function ActiveAgentBar({ agentName, isVisible }: { agentName?: string; isVisible: boolean }) {
  const cfg = getAgentCfg(agentName);
  const verb = agentStreamVerb(agentName);
  const [elapsed, setElapsed] = useState(0);

  // Elapsed time counter — ticks every second while visible
  useEffect(() => {
    if (!isVisible) { setElapsed(0); return; }
    setElapsed(0);
    const t = setInterval(() => setElapsed(s => s + 1), 1000);
    return () => clearInterval(t);
  }, [isVisible, agentName]);

  if (!isVisible) return null;

  const elapsedStr = elapsed < 60 ? `${elapsed}s` : `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`;

  return (
    <div
      className="active-agent-bar-enter"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '7px 20px',
        borderTop: `1px solid ${cfg.color}30`,
        background: `linear-gradient(90deg, ${cfg.color}08, transparent)`,
        fontFamily: 'var(--font-ui)',
        boxShadow: `inset 0 1px 0 ${cfg.color}18`,
      }}
    >
      <PulsingDot color={cfg.color} size={5} />
      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
        <span style={{ color: cfg.color, fontWeight: 600 }}>{cfg.label}</span>
        {' '}is {verb}
      </span>
      <span style={{
        marginLeft: 'auto',
        fontSize: 10.5,
        color: 'var(--text-dim)',
        fontFamily: 'var(--font-mono)',
        letterSpacing: '0.03em',
      }}>
        {elapsedStr}
      </span>
    </div>
  );
}

// ─── Typing Indicator (3-dot bounce — shown before first token) ───────────────

function TypingIndicator({ color = '#818cf8' }: { color?: string }) {
  return (
    <div className="typing-indicator">
      <span style={{ background: color }} />
      <span style={{ background: color }} />
      <span style={{ background: color }} />
    </div>
  );
}

// ─── Scroll-to-Bottom Button ──────────────────────────────────────────────
function ScrollToBottomButton({ onClick, unreadCount }: { onClick: () => void; unreadCount?: number }) {
  return (
    <button
      type="button"
      className="scroll-to-bottom-btn"
      onClick={onClick}
    >
      <ArrowRight size={11} style={{ transform: 'rotate(90deg)' }} />
      {unreadCount && unreadCount > 0 ? `${unreadCount} new` : 'New messages'}
      {unreadCount && unreadCount > 0 && (
        <span className="unread-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
      )}
    </button>
  );
}

// ─── Stall Warning ───────────────────────────────────────────────────────
function StallWarning() {
  return (
    <div className="stall-warning">
      <Loader2 size={11} style={{ animation: 'spinSlow 1.5s linear infinite' }} />
      Still working…
    </div>
  );
}



// ─── Progress Block (live file-writing progress bar) ─────────────────────────

function ProgressBlock({ message }: { message: ChatMessage }) {
  const done = message.eventData?.done ?? 0;
  const total = message.eventData?.total ?? 0;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  const currentFile = message.eventData?.currentFile as string | undefined;

  return (
    <div style={{ padding: '10px 20px', borderBottom: '1px solid var(--border-subtle)', animation: 'fadeSlideUp 0.3s ease' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9, marginBottom: 8 }}>
        <PulsingDot color="#6366f1" size={6} />
        <span style={{ fontSize: 12.5, fontWeight: 600, color: 'rgba(255,255,255,0.70)', fontFamily: 'var(--font-ui)' }}>
          Generating files
        </span>
        <span style={{ marginLeft: 'auto', fontSize: 11.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          {done}/{total}
        </span>
      </div>

      {/* Gradient progress track */}
      <div style={{ height: 3, borderRadius: 99, background: 'rgba(255,255,255,0.07)', overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${pct}%`,
          borderRadius: 99,
          background: 'linear-gradient(90deg, #6366f1, #34d399)',
          transition: 'width 0.4s ease',
        }} />
      </div>

      {/* Current file name */}
      {currentFile && (
        <div style={{ marginTop: 6, fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {currentFile}
        </div>
      )}
    </div>
  );
}

// ─── Done Banner (pipeline complete with file count) ──────────────────────────

function DoneBanner({ message }: { message: ChatMessage }) {
  const fileCount = message.eventData?.fileCount ?? 0;
  const durationMs = message.eventData?.duration as number | undefined;

  return (
    <div style={{ padding: '10px 20px', borderBottom: '1px solid var(--border-subtle)', animation: 'fadeSlideUp 0.3s ease' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 16px',
        borderRadius: 10,
        background: 'rgba(52,211,153,0.07)',
        border: '1px solid rgba(52,211,153,0.22)',
      }}>
        <CheckCircle2 size={14} style={{ color: '#34d399', flexShrink: 0 }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: 'rgba(255,255,255,0.78)', fontFamily: 'var(--font-ui)' }}>
          Pipeline complete
        </span>
        {fileCount > 0 && (
          <>
            <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>·</span>
            <span style={{ fontSize: 12.5, color: '#34d399', fontFamily: 'var(--font-mono)' }}>
              {fileCount} file{fileCount !== 1 ? 's' : ''} generated
            </span>
          </>
        )}
        {durationMs && (
          <>
            <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>·</span>
            <span style={{ fontSize: 11.5, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              {formatDuration(durationMs)}
            </span>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Message Bubble (user & general assistant) ──────────────────────────────

const MessageBubble = memo(function MessageBubble({ message, isLast, onRegen }: { message: ChatMessage; isLast?: boolean; onRegen?: () => void }) {
  const isUser = message.role === 'user';

  // The stream placeholder is intentionally empty; use the dedicated typing indicator instead.
  if (!isUser && message.isStreaming && !message.content.trim() && (!message.files || message.files.length === 0)) {
    return null;
  }

  // Route to specialized bubbles
  if (!isUser && message.messageType === 'thinking') {
    // Agent speech bubble — conversational, fully visible, not a collapsed log box
    return <AgentSpeechBubble message={message} isLast={isLast} onRegen={onRegen} />;
  }
  if (!isUser && message.messageType === 'code') {
    return <CodeBlock message={message} />;
  }
  if (!isUser && message.messageType === 'status') {
    return <StatusPill message={message} />;
  }
  if (!isUser && message.messageType === 'error') {
    return <ErrorBlock message={message} />;
  }
  if (!isUser && message.messageType === 'event_card') {
    return <EventCardBubble message={message} />;
  }
  if (!isUser && message.messageType === 'discussion') {
    return <DiscussionBubble message={message} />;
  }
  if (!isUser && (message.messageType === 'agent_status' || message.messageType === 'agent_result')) {
    return <AgentStatusBubble message={message} />;
  }
  if (!isUser && message.messageType === 'progress') {
    return <ProgressBlock message={message} />;
  }
  if (!isUser && message.messageType === 'done') {
    return <DoneBanner message={message} />;
  }

  // ── System message (validation warnings, errors, etc.) ──────────────────
  if (message.role === 'system') {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '8px 20px',
        borderBottom: '1px solid var(--border-subtle)',
        animation: 'fadeSlideUp 0.25s ease',
      }}>
        <AlertCircle size={14} style={{ color: '#f59e0b', flexShrink: 0 }} />
        <span style={{
          fontSize: 12.5,
          color: 'rgba(255,255,255,0.65)',
          fontFamily: 'var(--font-ui)',
        }}>
          {message.content}
        </span>
      </div>
    );
  }

  // ── User bubble ──────────────────────────────────────────────────────────
  if (isUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)', animation: 'fadeSlideUp 0.3s ease' }}>
        <div style={{ maxWidth: '78%' }}>
          <div style={{
            background: 'linear-gradient(135deg, rgba(99,102,241,0.18), rgba(99,102,241,0.08))',
            border: '1px solid rgba(99,102,241,0.28)',
            borderRadius: '16px 16px 4px 16px',
            padding: '12px 16px',
            fontSize: 'var(--text-base)',
            lineHeight: 'var(--leading-normal)',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-ui)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}>
            {message.content}
          </div>
          {/* Delivery status */}
          {message.deliveryStatus && (
            <div className={`delivery-status ${message.deliveryStatus}`} style={{ justifyContent: 'flex-end' }}>
              {message.deliveryStatus === 'pending' && (
                <>
                  <Loader2 size={9} style={{ animation: 'spinSlow 1s linear infinite' }} />
                  <span>Sending</span>
                </>
              )}
              {message.deliveryStatus === 'sent' && (
                <>
                  <CheckCircle2 size={9} />
                  <span>Delivered</span>
                </>
              )}
              {message.deliveryStatus === 'error' && (
                <>
                  <AlertCircle size={9} />
                  <span>Failed</span>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Team member general message ───────────────────────────────────────────
  const cfg = getAgentCfg(message.agentName);
  const streamLabel = message.isStreaming
    ? agentStreamVerb(message.agentName)
    : undefined;
  return (
    <AgentRow name={message.agentName} isStreaming={message.isStreaming} streamLabel={streamLabel}>
      <div style={{
        fontSize: 'var(--text-md)',
        lineHeight: 'var(--leading-normal)',
        color: 'var(--text-primary)',
        fontFamily: 'var(--font-ui)',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}>
        {message.content}
        {message.isStreaming && !message.content && <BlinkCursor on color={cfg.color} />}
      </div>

      {/* File badges */}
      {message.files && message.files.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-3 pt-2.5" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          {message.files.map((f) => (
            <span
              key={f.path}
              className={cn(
                "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10.5px] font-medium",
                f.status === 'done'
                  ? "bg-emerald-500/12 text-emerald-400 border border-emerald-500/25"
                  : "bg-blue-500/12 text-blue-400 border border-blue-500/25"
              )}
            >
              <Code2 size={11} />
              {f.path.split('/').pop() ?? f.path}
            </span>
          ))}
        </div>
      )}
    </AgentRow>
  );
}, (prev, next) =>
  // Only re-render when message content, streaming state, files, or isLast changes
  prev.message.id === next.message.id &&
  prev.message.isStreaming === next.message.isStreaming &&
  prev.message.content === next.message.content &&
  prev.message.deliveryStatus === next.message.deliveryStatus &&
  prev.message.files === next.message.files &&
  prev.isLast === next.isLast
);

// ─── Agent Typing Row ────────────────────────────────────────────────────────
// Shown for ~500ms before the thinking bubble appears — confirms agent started.

function AgentTypingRow({ agent }: { agent: { name: string; icon: string } }) {
  const cfg = getAgentCfg(agent.name);
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 13,
      padding: '12px 20px',
      borderBottom: '1px solid var(--border-subtle)',
      animation: 'fadeSlideUp 0.2s ease both',
    }}>
      <AgentAvatarBox name={agent.name} isStreaming />
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 13.5, fontWeight: 700, color: cfg.color, fontFamily: 'var(--font-ui)' }}>
          {cfg.label}
        </span>
        <div className="typing-indicator" style={{ padding: '0 0 0 4px' }}>
          <span style={{ background: cfg.color }} />
          <span style={{ background: cfg.color }} />
          <span style={{ background: cfg.color }} />
        </div>
      </div>
    </div>
  );
}

// ─── Pre-Stream Waiting Indicator ────────────────────────────────────────────
// Simple pulsing spinner shown while waiting for the first backend event.
// Unmounts the moment real agent bubbles arrive.

function PreStreamWaiting() {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 13,
      padding: '16px 20px',
      borderBottom: '1px solid var(--border-subtle)',
      animation: 'fadeSlideUp 0.3s ease both',
    }}>
      {/* Pulsing avatar placeholder */}
      <div style={{
        width: 36, height: 36, borderRadius: 10, flexShrink: 0,
        background: 'rgba(99,102,241,0.08)',
        border: '1.5px solid rgba(99,102,241,0.18)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Loader2
          size={16}
          style={{ color: '#818cf8', animation: 'spinSlow 1.1s linear infinite' }}
        />
      </div>

      {/* Text + typing dots */}
      <div>
        <div style={{
          fontSize: 13,
          fontWeight: 600,
          color: 'rgba(255,255,255,0.42)',
          fontFamily: 'var(--font-ui)',
          marginBottom: 5,
        }}>
          Getting your team ready
        </div>
        <div className="typing-indicator" style={{ padding: 0 }}>
          <span /><span /><span />
        </div>
      </div>
    </div>
  );
}

// Alias kept so existing JSX reference does not need to change
const PreStreamAgentCycle = PreStreamWaiting;

// ─── Message ID Generation & Deduplication ────────────────────────────────────
// Generates stable, incrementing message IDs within a session
// Prevents duplicate messages if backend sends the same event twice

let _sessionMessageCounter = 0;

function generateMessageId(): string {
  return `msg_${Date.now()}_${++_sessionMessageCounter}`;
}

// ─── MessageList ─────────────────────────────────────────────────────────────
// Owns the scroll container, welcome screen, message rendering, typing
// indicator, pre-stream cycle, and scroll-to-bottom button.
// Extracted so AtomsChatPanel can focus on state/event orchestration only.

interface MessageListProps {
  isEmpty: boolean;
  isStreaming: boolean;
  visibleMessages: ChatMessage[];
  activeAgentName: string | undefined;
  streamPhase: string;
  unreadCount: number;
  typingAgent: { name: string; icon: string } | null;
  chatContainerRef: React.RefObject<HTMLDivElement>;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  isAtBottom: React.MutableRefObject<boolean>;
  onContainerScroll: () => void;
  onRegen: () => void;
  onScrollToBottom: () => void;
  /** Called when user clicks an example prompt card */
  onPromptSelect: (text: string) => void;
}

function MessageList({
  isEmpty,
  isStreaming,
  visibleMessages,
  activeAgentName,
  streamPhase,
  unreadCount,
  typingAgent,
  chatContainerRef,
  messagesEndRef,
  isAtBottom,
  onContainerScroll,
  onRegen,
  onScrollToBottom,
  onPromptSelect,
}: MessageListProps) {
  return (
    <>
      {/* Scrollable message area */}
      <div
        ref={chatContainerRef}
        onScroll={onContainerScroll}
        className={cn(
          "flex-1 min-h-0 chat-messages-scroll",
          isEmpty ? "overflow-hidden" : "overflow-y-auto py-4 pb-28"
        )}
      >
        {isEmpty ? (
          /* ── Welcome / empty state ── */
          <div className="flex flex-col h-full px-6">
            <div className="flex-1 flex flex-col items-center justify-center">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mb-6 border border-blue-500/30">
                <Sparkles size={28} className="text-blue-400" />
              </div>
              <h2 className="text-[26px] font-bold mb-3 tracking-tight text-center" style={{ color: 'var(--ide-text)', fontFamily: "var(--chat-font-ui, 'DM Sans', sans-serif)" }}>
                What do you want to build?
              </h2>
              <p className="text-[14px] mb-8 text-center max-w-[360px] leading-relaxed" style={{ color: 'var(--ide-text-muted)', fontFamily: "var(--chat-font-ui, 'DM Sans', sans-serif)" }}>
                Your team will collaborate in real-time to bring your vision to life.
              </p>

              {/* Agent pills */}
              <div className="flex flex-wrap justify-center gap-2 mb-8">
                {[
                  { name: 'Team Leader',       icon: Crown,    color: 'text-amber-400',  bg: 'bg-amber-500/10 border-amber-500/30' },
                  { name: 'Database Engineer', icon: Database, color: 'text-blue-400',   bg: 'bg-blue-500/10 border-blue-500/30' },
                  { name: 'Backend Engineer',  icon: Code2,    color: 'text-green-400',  bg: 'bg-green-500/10 border-green-500/30' },
                  { name: 'Frontend Engineer', icon: Layers,   color: 'text-cyan-400',   bg: 'bg-cyan-500/10 border-cyan-500/30' },
                  { name: 'QA Engineer',       icon: Shield,   color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/30' },
                ].map(({ name, icon: Icon, color, bg }) => (
                  <div key={name} className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[12px] font-medium", bg)}>
                    <Icon size={14} className={color} />
                    <span style={{ color: 'var(--ide-text-secondary)' }}>{name}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Example prompts */}
            <div className="pb-6">
              <p className="text-[11px] font-semibold uppercase tracking-wider mb-3 text-center" style={{ color: 'var(--ide-text-muted)' }}>
                Try an example
              </p>
              <div className="grid grid-cols-2 gap-2">
                {EXAMPLE_PROMPTS.map(({ icon: Icon, title, prompt, color }) => (
                  <button
                    type="button"
                    key={title}
                    onClick={() => onPromptSelect(prompt)}
                    className="flex items-start gap-3 p-3 rounded-xl border text-left transition-all hover:scale-[1.02] hover:border-blue-500/50"
                    style={{ background: 'var(--ide-surface)', borderColor: 'var(--ide-border)' }}
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
          /* ── Active conversation ── */
          <>
            {isStreaming && <AgentPresenceBar />}

            {visibleMessages.map((msg, i) => (
              <MessageErrorBoundary key={msg.id}>
                <MessageBubble
                  message={msg}
                  isLast={i === visibleMessages.length - 1}
                  onRegen={onRegen}
                />
              </MessageErrorBoundary>
            ))}

            {/* Agent typing row — shown briefly before the thinking bubble appears */}
            {typingAgent && <AgentTypingRow agent={typingAgent} />}

            {/* Pre-stream spinner — shown before first agent_start event fires */}
            {isStreaming && !typingAgent && !visibleMessages.some(m => m.messageType === 'thinking' && m.isStreaming) && (
              <PreStreamAgentCycle />
            )}

            {streamPhase === 'completed' && <CompletionCard />}
          </>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Scroll-to-bottom badge */}
      {isStreaming && !isAtBottom.current && (
        <ScrollToBottomButton
          unreadCount={unreadCount}
          onClick={onScrollToBottom}
        />
      )}
    </>
  );
}



export function AtomsChatPanel({ embedded }: { embedded?: boolean }) {
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [wsStatus, setWsStatus] = useState<'idle' | 'connecting' | 'connected' | 'disconnected' | 'error'>('idle');
  const [attachments, setAttachments] = useState<ChatAttachment[]>([]);
  const [activeAgentName, setActiveAgentName] = useState<string | undefined>(undefined);
  const [typingAgent, setTypingAgent] = useState<{ name: string; icon: string } | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const isAtBottom = useRef(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // File-progress tracking — mutable, no re-render needed
  const fileCountRef = useRef({ total: 0, done: 0 });
  const progressMsgIdRef = useRef<string | null>(null);
  const runStartRef = useRef<number>(0);
  // Message ID generation and deduplication for this session
  const messageIdCounterRef = useRef(0);
  const processedEventIdsRef = useRef<Set<string>>(new Set());

  // Per-session stream processing instances — avoids module-level shared state
  const narrativeDripRef = useRef(new NarrativeDrip());
  const msgQueueRef = useRef(new MessageQueue());
  // Tracks whether real backend tokens have taken over (per-agent lifetime)
  const usingRealTokensRef = useRef(false);

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
  const appendToLastThinkingMessage = useIDEStore((s) => s.appendToLastThinkingMessage);
  const clearLastThinkingMessage = useIDEStore((s) => s.clearLastThinkingMessage);
  const markLastThinkingMessageDone = useIDEStore((s) => s.markLastThinkingMessageDone);
  const appendToLastDiscussionMessage = useIDEStore((s) => s.appendToLastDiscussionMessage);
  const markLastDiscussionMessageDone = useIDEStore((s) => s.markLastDiscussionMessageDone);
  const updateChatMessage = useIDEStore((s) => s.updateChatMessage);
  const clearChat = useIDEStore((s) => s.clearChat);

  const atmosPhase = useAtmosStore((s) => s.phase);

  // Stream-store (mode toggle, agent presence, phase)
  const streamMode = useStreamStore((s) => s.mode);
  const streamPhase = useStreamStore((s) => s.phase);
  const thinkingLiveText = useStreamStore((s) => s.liveText);
  const isAgentActive = useStreamStore((s) => s.isAgentActive);

  // Chat search & filter
  const chatSearchQuery = useIDEStore((s) => s.chatSearchQuery);
  const chatAgentFilter = useIDEStore((s) => s.chatAgentFilter);

  // Track WebSocket lifecycle so we can show a connection status badge
  useEventBus('WS_STATUS', (event) => {
    const { status } = event.payload as { status: 'connecting' | 'connected' | 'disconnected' | 'error' };
    setWsStatus(status === 'connected' ? 'connected' : status);
    // Auto-clear 'connected' after 2s — no need to permanently show a green badge
    if (status === 'connected') {
      setTimeout(() => setWsStatus('idle'), 2000);
    }
  });

  // Show all message types that MessageBubble knows how to render.
  // Apply search query and agent filter when active.
  const visibleMessages = useMemo(() => {
    const searchLower = chatSearchQuery.trim().toLowerCase();
    return chatMessages.filter(m => {
      // Base visibility: all roles are visible
      if (m.role !== 'user' && m.role !== 'assistant' && m.role !== 'system') return false;

      // Agent filter: only show messages from selected agent (user messages always pass)
      if (chatAgentFilter && m.role === 'assistant' && m.agentName && m.agentName !== chatAgentFilter) {
        return false;
      }

      // Search filter: match against message content (all roles)
      if (searchLower && !m.content.toLowerCase().includes(searchLower)) {
        return false;
      }

      return true;
    });
  }, [chatMessages, chatSearchQuery, chatAgentFilter]);

  // Smart auto-scroll — only scroll to bottom when user hasn't scrolled up
  const scrollToBottom = useCallback(() => {
    if (isAtBottom.current && chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, []);

  const handleContainerScroll = useCallback(() => {
    const el = chatContainerRef.current;
    if (!el) return;
    const wasAtBottom = isAtBottom.current;
    isAtBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    // Reset unread count when user scrolls to bottom
    if (!wasAtBottom && isAtBottom.current) {
      setUnreadCount(0);
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages, aiStatus, scrollToBottom]);

  // Track unread messages when user is scrolled up
  const prevMsgCountRef = useRef(chatMessages.length);
  useEffect(() => {
    const newCount = chatMessages.length;
    const diff = newCount - prevMsgCountRef.current;
    prevMsgCountRef.current = newCount;
    if (diff > 0 && !isAtBottom.current) {
      setUnreadCount(c => c + diff);
    }
  }, [chatMessages.length]);

  // ─── Listen for ATMOS events ────────────────────────────────────────────
  useEffect(() => {
    const ide = () => useIDEStore.getState();

    // Wire LiveWriter to flush characters into the store
    liveWriter.setFlushCallback((path, chunk) => {
      ide().appendToFile(path, chunk);
    });

    // ── Agent thinking block lifecycle ───────────────────────────────────

    // AI_AGENT_ACTIVE → show typing indicator, then drip narrative into chat bubble
    const offAgentActive = EventBus.on('AI_AGENT_ACTIVE', (event) => {
      const { name, icon, thinking } = event.payload as { name: string; icon: string; thinking: string };

      // Mark the last pending user message as 'sent' — backend confirmed receipt
      const msgs = ide().chatMessages;
      let lastUserIdx = -1;
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === 'user') { lastUserIdx = i; break; }
      }
      if (lastUserIdx >= 0 && msgs[lastUserIdx].deliveryStatus === 'pending') {
        const updated = [...msgs];
        updated[lastUserIdx] = { ...updated[lastUserIdx], deliveryStatus: 'sent' };
        useIDEStore.setState({ chatMessages: updated });
      }

      // ① Reset per-agent streaming state
      usingRealTokensRef.current = false;
      narrativeDripRef.current.stop();

      // ② Show "agent is typing..." row while the thinking bubble isn't visible yet
      setTypingAgent({ name, icon });

      // ③ Initialize PhaseBlock live text (agent name + cursor)
      useStreamStore.getState().setLiveText('', name);

      // ④ After a short delay create the thinking bubble then start the narrative drip
      //    The 200ms gives the typing indicator time to appear before text starts
      setTimeout(() => {
        setTypingAgent(null);

        // Create thinking bubble — starts empty, narrative drip fills it immediately
        addChatMessage({
          role: 'assistant',
          content: '',
          isStreaming: true,
          agentName: name,
          agentIcon: icon,
          messageType: 'thinking',
        });
        setActiveAgentName(name);

        // Start dripping narrative into BOTH PhaseBlock AND the chat bubble
        if (thinking) {
          narrativeDripRef.current.start(thinking, (chunk) => {
            appendToLastThinkingMessage(chunk);
            useStreamStore.getState().appendLiveText(chunk);
          });
        }
      }, 200);
    });

    // AI_THINKING_TOKEN → real tokens from backend: cancel narrative drip, stream real text
    const thinkingDrip = new TokenDripBuffer((batch) => {
      appendToLastThinkingMessage(batch);
      // In real-token mode, also push to PhaseBlock live text
      if (usingRealTokensRef.current) {
        useStreamStore.getState().appendLiveText(batch);
      }
    });

    const chatDrip = new TokenDripBuffer((batch) => {
      appendToLastAssistantMessage(batch);
    });

    const offThinkingToken = EventBus.on('AI_THINKING_TOKEN', (event) => {
      const { token } = event.payload as { token: string };
      if (!token) return;

      if (!usingRealTokensRef.current) {
        // First real token — cancel the narrative drip, clear it from both PhaseBlock AND chat bubble
        usingRealTokensRef.current = true;
        narrativeDripRef.current.stop();
        clearLastThinkingMessage();
        const ss = useStreamStore.getState();
        ss.setLiveText('', ss.agentName);
      }
      thinkingDrip.push(token);
    });

    // AI_AGENT_DONE → stop all drips, mark done
    const offAgentDone = EventBus.on('AI_AGENT_DONE', () => {
      narrativeDripRef.current.stop();  // stop mid-narrative if agent finished fast
      thinkingDrip.drainAll((batch) => {
        appendToLastThinkingMessage(batch);
        if (usingRealTokensRef.current) useStreamStore.getState().appendLiveText(batch);
      });
      chatDrip.drainAll((batch) => {
        appendToLastAssistantMessage(batch);
      });
      markLastThinkingMessageDone();
      useStreamStore.getState().setAgentActive(false);
    });

    // Full chat messages from backend
    const offMsg = EventBus.on('AI_MESSAGE', (event) => {
      const { _eventId, content, agentName, agentIcon, messageType, eventType, eventData } = event.payload as {
        _eventId?: string; content: string; agentName?: string; agentIcon?: string; messageType?: string;
        eventType?: string; eventData?: Record<string, any>;
      };
      if (!content) return;

      // Use backend-assigned event ID for deduplication when available;
      // fall back to content hash for backwards compatibility with older backends.
      const dedupeKey = _eventId ?? `${messageType}_${agentName}_${content.slice(0, 50)}`;
      if (processedEventIdsRef.current.has(dedupeKey)) {
        return; // Skip duplicate
      }
      processedEventIdsRef.current.add(dedupeKey);

      // Normalize agent name using config (maps role keys like "Backend Engineer" to display label)
      const normalizedAgentName = agentName
        ? (AGENT_CFG_RICH[agentName]?.label ?? agentName)
        : agentName;

      const addMsg = () => addChatMessage({
        id: generateMessageId(),
        role: 'assistant',
        content,
        isStreaming: false,
        agentName: normalizedAgentName,
        agentIcon,
        messageType: (messageType as any) || 'chat',
        eventType,
        eventData,
      });

      // Pace event_card messages for cinematic rhythm — other types are immediate
      if (messageType === 'event_card') {
        msgQueueRef.current.enqueue(addMsg);
      } else {
        addMsg();
      }
    });

    // Streaming tokens
    const offToken = EventBus.on('AI_MESSAGE_TOKEN', (event) => {
      const { token } = event.payload as { token: string };
      if (token) {
        chatDrip.push(token);
      }
    });

    // Agent-to-agent discussions — appear one at a time with live typing animation
    const offDiscussion = EventBus.on('AI_DISCUSSION', (event) => {
      const { _eventId, from, to, icon, message } = event.payload as {
        _eventId?: string; from: string; to: string; icon: string; message: string;
      };
      if (!message) return;

      const dedupeKey = _eventId ?? `discussion_${from}_${to}_${message.slice(0, 50)}`;
      if (processedEventIdsRef.current.has(dedupeKey)) return;
      processedEventIdsRef.current.add(dedupeKey);

      const normalizedFrom = getAgentCfg(from).label;
      const normalizedTo = getAgentCfg(to).label;

      // Enqueue so discussions don't pile up on top of each other
      msgQueueRef.current.enqueue(() => {
        // ① Create empty streaming discussion bubble
        addChatMessage({
          id: generateMessageId(),
          role: 'assistant',
          content: '',
          isStreaming: true,
          agentName: normalizedFrom,
          agentIcon: icon,
          toAgent: normalizedTo,
          messageType: 'discussion',
        });

        // ② Drip the message text char-by-char into the bubble
        const drip = new NarrativeDrip();
        drip.start(message, (chunk) => {
          appendToLastDiscussionMessage(chunk);
        });

        // ③ Mark done after full text has been dripped
        //    NarrativeDrip speed: ~4 chars per 20ms → 5ms per char median
        const dripDurationMs = message.length * 6 + 150;
        setTimeout(() => {
          markLastDiscussionMessageDone();
        }, dripDurationMs);
      });
    });

    // ── AI starts writing a file: pre-create the tab + update progress ──
    const offFileWriting = EventBus.on('AI_FILE_WRITING', (event) => {
      const { path } = event.payload as { path: string };
      const state = ide();

      if (!state.openFiles.includes(path)) {
        state.createFile(path, '', true);
        state.setAIStatus('generating');
        state.setAICurrentFile(path);
      }
      state.setFileLiveWriting(path, true);

      // Track file in stream-store for developer-mode file tree
      useStreamStore.getState().trackFile(path);

      // Increment total and create/update progress message
      fileCountRef.current.total += 1;
      const { total, done } = fileCountRef.current;
      if (!progressMsgIdRef.current) {
        const pid = Math.random().toString(36).slice(2, 11);
        progressMsgIdRef.current = pid;
        addChatMessage({
          id: pid,
          role: 'assistant',
          content: '',
          messageType: 'progress',
          eventData: { total, done, currentFile: path },
        });
      } else {
        updateChatMessage(progressMsgIdRef.current, {
          eventData: { total, done, currentFile: path },
        });
      }
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
      const existingContent = state.fileContents[path] ?? '';
      const finalContent = content && content.length > 0 ? content : existingContent;
      state.createFile(path, finalContent, true);
      state.setFileLiveWriting(path, false);

      // Update chat message with file badge
      const msgs = [...state.chatMessages];
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === 'assistant' && msgs[i].messageType !== 'progress') {
          const files = [...(msgs[i].files || [])];
          if (!files.find(f => f.path === path)) {
            files.push({ path, status: 'done' });
          }
          msgs[i] = { ...msgs[i], files };
          break;
        }
      }
      useIDEStore.setState({ chatMessages: msgs });

      // Track completion in stream-store for developer-mode file tree
      useStreamStore.getState().markFileDone(path);

      // Increment done count and update progress bar
      fileCountRef.current.done += 1;
      if (progressMsgIdRef.current) {
        const { total, done } = fileCountRef.current;
        updateChatMessage(progressMsgIdRef.current, {
          eventData: { total, done, currentFile: path },
        });
      }
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
      // Flush all queued narrative messages immediately
      msgQueueRef.current.flush();
      // Drain token drip buffer and flush live writer
      thinkingDrip.drainAll((batch) => {
        appendToLastThinkingMessage(batch);
        useStreamStore.getState().appendLiveText(batch);
      });
      chatDrip.drainAll((batch) => {
        appendToLastAssistantMessage(batch);
      });
      liveWriter.flush();

      // Stop narrative drip + mark live text inactive (cursor off)
      narrativeDripRef.current.stop();
      useStreamStore.getState().setAgentActive(false);

      setIsStreaming(false);
      setAIStatus('idle');
      setActiveAgentName(undefined);
      setTypingAgent(null);
      const { total } = fileCountRef.current;
      const durationMs = Date.now() - runStartRef.current;
      if (progressMsgIdRef.current) {
        updateChatMessage(progressMsgIdRef.current, {
          messageType: 'done',
          eventData: { fileCount: total, duration: durationMs },
        });
        progressMsgIdRef.current = null;
      } else if (total > 0) {
        addChatMessage({
          role: 'assistant',
          content: '',
          messageType: 'done',
          eventData: { fileCount: total, duration: durationMs },
        });
      }
      fileCountRef.current = { total: 0, done: 0 };

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
        const filesForDb = { ...state.fileContents };

        // Persist project to backend
        apiFetch<{ id: string; name: string }>('/projects/', {
          method: 'POST',
          body: JSON.stringify({ name: projectName, idea: firstUserMsg?.content || '' }),
        })
          .then(async (saved) => {
            setProject({ id: saved.id, name: saved.name });

            try {
              await apiFetch<{
                project_id: string;
                saved: number;
                skipped_invalid_path: number;
                skipped_too_large: number;
              }>(`/artifacts/${saved.id}/sync`, {
                method: 'POST',
                body: JSON.stringify({
                  files: filesForDb,
                  replace_existing: true,
                }),
              });
            } catch (syncError) {
              console.warn('Failed to sync generated files to DB artifacts:', syncError);
            }
          })
          .catch(() => {
            // Fallback to local-only project if not authenticated or API fails
            setProject({ id: 'generated', name: projectName });
          });

        setWorkspaceMode('project');
      }
    });

    return () => {
      liveWriter.reset();
      liveWriter.setFlushCallback(null);
      thinkingDrip.reset();
      chatDrip.reset();
      narrativeDripRef.current.reset();
      msgQueueRef.current.reset();
      offAgentActive();
      offThinkingToken();
      offAgentDone();
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

    // Validate attachments before sending
    const validation = validateAttachmentsForSend(attachments);
    if (!validation.valid) {
      addChatMessage({
        role: 'system',
        content: validation.error || 'Invalid attachments',
        isStreaming: false,
      });
      return;
    }

    // Reset file-progress tracking for this run
    fileCountRef.current = { total: 0, done: 0 };
    progressMsgIdRef.current = null;
    runStartRef.current = Date.now();

    // Clear deduplication set for new run
    processedEventIdsRef.current.clear();

    // Build message content including attachments
    let messageContent = text;
    if (attachments.length > 0) {
      const attachmentContext = attachments
        .map(a => `[Attached: ${a.name} (${a.type})]:\n${a.content.slice(0, 2000)}`)
        .join('\n\n');
      messageContent = `${text}\n\n---\n${attachmentContext}`;
    }

    // Add user message with attachment metadata
    addChatMessage({
      role: 'user',
      content: text,
      files: attachments.map(a => ({ path: a.name, status: 'done' as const })),
      deliveryStatus: 'pending',
    });
    setInput("");
    setAttachments([]);
    setIsStreaming(true);
    setAIStatus('thinking');

    // Fire the NIM multi-agent pipeline — agent thinking bubbles appear via AI_AGENT_ACTIVE events
    try {
      await runNimIntent(messageContent);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      updateLastAssistantMessage(`Connection error: ${msg}. Make sure the backend is running.`);
      // Mark user message as delivery error
      const msgs = useIDEStore.getState().chatMessages;
      let lastUserIdx = -1;
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (msgs[i].role === 'user') { lastUserIdx = i; break; }
      }
      if (lastUserIdx >= 0 && msgs[lastUserIdx].deliveryStatus === 'pending') {
        const updated = [...msgs];
        updated[lastUserIdx] = { ...updated[lastUserIdx], deliveryStatus: 'error' };
        useIDEStore.setState({ chatMessages: updated });
      }
      setAIStatus('error');
    } finally {
      // Always reset streaming state — prevents stuck UI if ATMOS_DONE didn't fire
      setIsStreaming(false);
    }
  }, [input, isStreaming, attachments, addChatMessage, setAIStatus, updateLastAssistantMessage]);

  const handleStop = useCallback(() => {
    const ac = useAtmosStore.getState().abortController;
    if (ac) ac.abort();
    useAtmosStore.getState().reset();
    setIsStreaming(false);
    setAIStatus('idle');
  }, []);

  // ─── Clear conversation ───────────────────────────────────────────────────────
  const handleClear = useCallback(() => {
    clearChat();
    setIsStreaming(false);
    setAIStatus('idle');
    setActiveAgentName(undefined);
    setTypingAgent(null);
    fileCountRef.current = { total: 0, done: 0 };
    progressMsgIdRef.current = null;
    processedEventIdsRef.current.clear();
    narrativeDripRef.current.reset();
    msgQueueRef.current.reset();
  }, [clearChat, setAIStatus]);

  // ─── Regenerate last response ──────────────────────────────────────────────
  const handleRegen = useCallback(async () => {
    if (isStreaming) return;
    // Find last user message
    const allMsgs = useIDEStore.getState().chatMessages;
    const lastUser = [...allMsgs].reverse().find(m => m.role === 'user');
    if (!lastUser) return;
    // Remove all messages after the last user message
    const lastUserIdx = allMsgs.lastIndexOf(lastUser);
    const trimmed = allMsgs.slice(0, lastUserIdx + 1);
    useIDEStore.setState({ chatMessages: trimmed });
    // Reset progress tracking
    fileCountRef.current = { total: 0, done: 0 };
    progressMsgIdRef.current = null;
    processedEventIdsRef.current.clear();
    runStartRef.current = Date.now();
    setIsStreaming(true);
    setAIStatus('thinking');
    try {
      await runNimIntent(lastUser.content);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      updateLastAssistantMessage(`Connection error: ${msg}. Make sure the backend is running.`);
      setAIStatus('error');
      setIsStreaming(false);
    }
  }, [isStreaming, setAIStatus, updateLastAssistantMessage]);

  // ─── Attachment Handlers ───────────────────────────────────────────────────────

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    let totalSize = 0;
    const newAttachments: ChatAttachment[] = [];

    Array.from(files).forEach((file) => {
      // Validate file size
      if (file.size > MAX_FILE_SIZE) {
        addChatMessage({
          role: 'system',
          content: `⚠️ File "${file.name}" exceeds 10MB limit (${(file.size / 1024 / 1024).toFixed(1)}MB)`,
          isStreaming: false,
        });
        return;
      }

      totalSize += file.size;

      // Validate MIME type
      if (file.type && !ALLOWED_MIME_TYPES.has(file.type) && !file.name.match(/\.(py|js|ts|tsx|jsx|md|json|yaml|html|css|xml)$/i)) {
        addChatMessage({
          role: 'system',
          content: `⚠️ File type not supported: ${file.type || file.name.split('.').pop()}`,
          isStreaming: false,
        });
        return;
      }

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
          mimeType: file.type,
        };
        newAttachments.push(attachment);
        setAttachments(prev => [...prev, attachment]);
      };
      reader.onerror = () => {
        addChatMessage({
          role: 'system',
          content: `⚠️ Failed to read file: ${file.name}`,
          isStreaming: false,
        });
      };
      reader.readAsText(file);
    });

    // Validate total size
    if (totalSize > MAX_TOTAL_SIZE) {
      addChatMessage({
        role: 'system',
        content: `⚠️ Total attachments exceed 25MB limit (${(totalSize / 1024 / 1024).toFixed(1)}MB)`,
        isStreaming: false,
      });
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [addChatMessage]);

  const removeAttachment = useCallback((id: string) => {
    setAttachments(prev => prev.filter(att => att.id !== id));
  }, []);

  // ─── Prompt selection (from welcome screen example prompts) ──────────────────
  const handlePromptSelect = useCallback((text: string) => {
    setInput(text);
    setTimeout(() => textareaRef.current?.focus(), 0);
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

      {/* WebSocket connection status — only shown when there's an issue */}
      {(wsStatus === 'connecting' || wsStatus === 'disconnected' || wsStatus === 'error') && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '5px 16px',
          background: wsStatus === 'error' || wsStatus === 'disconnected'
            ? 'rgba(248,113,113,0.08)' : 'rgba(251,191,36,0.08)',
          borderBottom: wsStatus === 'error' || wsStatus === 'disconnected'
            ? '1px solid rgba(248,113,113,0.20)' : '1px solid rgba(251,191,36,0.20)',
          fontSize: 11.5,
          fontFamily: 'var(--font-ui)',
          color: wsStatus === 'error' || wsStatus === 'disconnected'
            ? 'rgba(248,113,113,0.85)' : 'rgba(251,191,36,0.85)',
        }}>
          {wsStatus === 'connecting' && (
            <><Loader2 size={11} style={{ animation: 'spinSlow 1s linear infinite', flexShrink: 0 }} /> Connecting to backend…</>
          )}
          {wsStatus === 'disconnected' && (
            <><AlertCircle size={11} style={{ flexShrink: 0 }} /> Connection lost — try sending again</>
          )}
          {wsStatus === 'error' && (
            <><AlertCircle size={11} style={{ flexShrink: 0 }} /> Backend unreachable — is the server running?</>
          )}
        </div>
      )}

      {/* Messages or Welcome */}
      <MessageList
        isEmpty={isEmpty}
        isStreaming={isStreaming}
        visibleMessages={visibleMessages}
        activeAgentName={activeAgentName}
        streamPhase={streamPhase}
        unreadCount={unreadCount}
        typingAgent={typingAgent}
        chatContainerRef={chatContainerRef}
        messagesEndRef={messagesEndRef}
        isAtBottom={isAtBottom}
        onContainerScroll={handleContainerScroll}
        onRegen={handleRegen}
        onScrollToBottom={() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
          setUnreadCount(0);
        }}
        onPromptSelect={handlePromptSelect}
      />

      {/* Input Area */}
      <InputArea
        input={input}
        setInput={setInput}
        isStreaming={isStreaming}
        attachments={attachments}
        chatMessagesCount={chatMessages.length}
        textareaRef={textareaRef}
        fileInputRef={fileInputRef}
        onSend={handleSend}
        onStop={handleStop}
        onClear={handleClear}
        onFileUpload={handleFileUpload}
        onRemoveAttachment={removeAttachment}
      />
    </aside>
  );
}
