/**
 * AgentPresenceBar — Persistent top bar showing all 6 agents with live status.
 *
 * Status variants:
 *   idle      → muted chip, faded
 *   thinking  → pulsing dot, subtle glow
 *   working   → animated dot, glowing border
 *   reviewing → amber dot
 *   done      → green check, dimmed
 */

import { useStreamStore, type AgentPresence, type AgentStatus } from '@/streaming/stream-store';

// ─── Status Dot ───────────────────────────────────────────────────────────────

function StatusDot({ status, color }: { status: AgentStatus; color: string }) {
  if (status === 'idle') {
    return (
      <span
        aria-hidden
        style={{
          width: 5, height: 5, minWidth: 5,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.18)',
          display: 'inline-block',
          flexShrink: 0,
        }}
      />
    );
  }
  if (status === 'done') {
    return (
      <span
        aria-hidden
        style={{
          width: 5, height: 5, minWidth: 5,
          borderRadius: '50%',
          background: '#34d399',
          display: 'inline-block',
          flexShrink: 0,
        }}
      />
    );
  }
  // thinking / working / reviewing — animated
  return (
    <span
      aria-hidden
      style={{
        width: 5, height: 5, minWidth: 5,
        borderRadius: '50%',
        background: color,
        boxShadow: `0 0 8px ${color}`,
        display: 'inline-block',
        flexShrink: 0,
        animation: 'pulse 1.3s ease-in-out infinite',
      }}
    />
  );
}

// ─── Single Agent Chip ────────────────────────────────────────────────────────

function AgentChip({ agent }: { agent: AgentPresence }) {
  const isActive = agent.status === 'working' || agent.status === 'thinking' || agent.status === 'reviewing';
  const isDone   = agent.status === 'done';
  const isIdle   = agent.status === 'idle';

  return (
    <div
      title={`${agent.name}${agent.model ? ` (${agent.model})` : ''}: ${agent.status}`}
      style={{
        display:        'flex',
        alignItems:     'center',
        gap:            5,
        padding:        '4px 10px',
        borderRadius:   20,
        border:         `1px solid ${isActive ? `${agent.color}50` : 'transparent'}`,
        background:     isActive ? `${agent.color}0d` : 'transparent',
        boxShadow:      isActive ? `0 0 14px ${agent.color}28` : 'none',
        opacity:        isIdle ? 0.28 : isDone ? 0.55 : 1,
        transition:     'all 0.35s ease',
        whiteSpace:     'nowrap',
        cursor:         'default',
        userSelect:     'none',
      }}
    >
      {/* Avatar monogram */}
      <span style={{
        fontSize:    9.5,
        fontWeight:  700,
        fontFamily:  'var(--font-mono)',
        letterSpacing: '0.04em',
        color:       isActive ? agent.color : 'rgba(255,255,255,0.35)',
        transition:  'color 0.3s ease',
      }}>
        {agent.avatar}
      </span>

      {/* Name + Model */}
      <span style={{
        display:     'flex',
        flexDirection: 'column',
        lineHeight:  1.15,
      }}>
        <span style={{
          fontSize:    11,
          fontWeight:  isActive ? 600 : 400,
          fontFamily:  'var(--font-ui)',
          color:       isActive ? agent.color : isDone ? 'rgba(255,255,255,0.40)' : 'rgba(255,255,255,0.25)',
          transition:  'color 0.3s ease',
          letterSpacing: '0.01em',
        }}>
          {agent.name}
        </span>
        {agent.model && (isActive || isDone) && (
          <span style={{
            fontSize:    8,
            fontWeight:  400,
            fontFamily:  'var(--font-mono)',
            color:       isActive ? `${agent.color}99` : 'rgba(255,255,255,0.22)',
            transition:  'color 0.3s ease',
            letterSpacing: '0.02em',
          }}>
            {agent.model}
          </span>
        )}
      </span>

      {/* Status indicator */}
      {isDone ? (
        <span style={{ fontSize: 9, color: '#34d399', fontWeight: 700 }}>✓</span>
      ) : (
        <StatusDot status={agent.status} color={agent.color} />
      )}
    </div>
  );
}

// ─── Connector line between chips ─────────────────────────────────────────────

function Connector() {
  return (
    <div style={{
      width: 12,
      height: 1,
      background: 'rgba(255,255,255,0.06)',
      flexShrink: 0,
    }} />
  );
}

// ─── Agent Presence Bar ───────────────────────────────────────────────────────

export function AgentPresenceBar() {
  const agents = useStreamStore(s => s.agents);

  return (
    <div
      className="agent-presence-bar"
      role="status"
      aria-label="Agent pipeline status"
    >
      {agents.map((agent, i) => (
        <span key={agent.id} style={{ display: 'contents' }}>
          <AgentChip agent={agent} />
          {i < agents.length - 1 && <Connector />}
        </span>
      ))}
    </div>
  );
}
