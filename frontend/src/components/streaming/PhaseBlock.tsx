/**
 * PhaseBlock — Cinematic phase-driven execution display.
 *
 * Replaces the agent speech bubble flood in simple mode.
 * Shows:
 *  1. Phase label + dot trail + progress bar
 *  2. Checkpoints (✔ done / → pending)
 *  3. Live agent text — tokens stream in real-time under the phase header
 *
 * Shown:  isStreaming && mode === 'simple'
 * Hidden: dev / debug mode (raw messages shown there instead)
 */

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useStreamStore } from '@/streaming/stream-store';
import { PHASE_ORDER, PHASE_LABELS, PHASE_COLORS } from '@/streaming/phase-engine';

// ─── Blinking block cursor ─────────────────────────────────────────────────────

function LiveCursor({ on, color }: { on: boolean; color: string }) {
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    if (!on) { setVisible(true); return; }
    const t = setInterval(() => setVisible(v => !v), 530);
    return () => clearInterval(t);
  }, [on]);
  if (!on) return null;
  return (
    <span aria-hidden style={{
      opacity:    visible ? 1 : 0,
      color,
      fontWeight: 700,
      fontSize:   '0.95em',
      userSelect: 'none',
      transition: 'opacity 80ms',
      marginLeft: 1,
    }}>
      ▍
    </span>
  );
}

// ─── Live streaming text area ─────────────────────────────────────────────────
// Shows agent tokens as they stream in, scrolled to the tail.

function LiveTextArea({ color }: { color: string }) {
  const liveText      = useStreamStore(s => s.liveText);
  const isAgentActive = useStreamStore(s => s.isAgentActive);
  const agentName     = useStreamStore(s => s.agentName);
  const scrollRef     = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom as text grows
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [liveText]);

  if (!liveText) return null;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      style={{
        borderTop:   '1px solid rgba(255,255,255,0.05)',
        paddingTop:  12,
        marginTop:   2,
      }}
    >
      {/* Agent name label */}
      {agentName && (
        <div style={{
          display:      'flex',
          alignItems:   'center',
          gap:          6,
          marginBottom: 7,
        }}>
          <span style={{
            fontSize:   10,
            fontWeight: 700,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            color:      `${color}80`,
            fontFamily: 'var(--font-ui)',
          }}>
            {agentName}
          </span>
          {isAgentActive && (
            <span style={{
              display:      'inline-block',
              width:         5,
              height:        5,
              borderRadius: '50%',
              background:   color,
              boxShadow:    `0 0 6px ${color}`,
              animation:    'pulse 1.3s ease infinite',
              flexShrink:   0,
            }} />
          )}
        </div>
      )}

      {/* Streaming text — scrollable, shows tail */}
      <div
        ref={scrollRef}
        style={{
          maxHeight:  '9em',        // ~5–6 visible lines
          overflowY:  'auto',
          scrollbarWidth: 'none',
          fontSize:   13,
          lineHeight: 1.72,
          color:      isAgentActive
            ? 'rgba(255,255,255,0.80)'
            : 'rgba(255,255,255,0.38)',
          fontFamily: 'var(--font-ui)',
          whiteSpace: 'pre-wrap',
          wordBreak:  'break-word',
          borderLeft: `2px solid ${isAgentActive ? color : 'rgba(255,255,255,0.06)'}`,
          paddingLeft: 11,
          transition: 'color 0.5s ease, border-color 0.5s ease',
        }}
      >
        {liveText}
        <LiveCursor on={isAgentActive} color={color} />
      </div>
    </motion.div>
  );
}

// ─── PhaseBlock ────────────────────────────────────────────────────────────────

export function PhaseBlock() {
  const phase       = useStreamStore(s => s.phase);
  const progress    = useStreamStore(s => s.progress);
  const checkpoints = useStreamStore(s => s.checkpoints);

  const color    = PHASE_COLORS[phase];
  const phaseIdx = PHASE_ORDER.indexOf(phase);

  // Visible phases (exclude 'completed' — CompletionCard handles that state)
  const dotPhases = PHASE_ORDER.filter(p => p !== 'completed');

  return (
    <motion.div
      key={phase}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      style={{
        margin:        '10px 20px 4px',
        background:    'rgba(10,10,12,0.92)',
        border:        `1px solid ${color}20`,
        borderRadius:  14,
        padding:       '16px 18px',
        display:       'flex',
        flexDirection: 'column',
        gap:           12,
      }}
    >
      {/* ── Phase header ──────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Phase dot trail */}
          <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
            {dotPhases.map((p, i) => (
              <div
                key={p}
                style={{
                  width:        i === phaseIdx ? 7 : 5,
                  height:       i === phaseIdx ? 7 : 5,
                  borderRadius: '50%',
                  background:   i < phaseIdx
                    ? PHASE_COLORS[p]
                    : i === phaseIdx
                    ? color
                    : 'rgba(255,255,255,0.08)',
                  transition:   'all 0.4s ease',
                  boxShadow:    i === phaseIdx ? `0 0 8px ${color}80` : 'none',
                  flexShrink:   0,
                }}
              />
            ))}
          </div>

          {/* Phase label */}
          <span style={{
            fontSize:      11,
            fontWeight:    700,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color,
            fontFamily:    'var(--font-ui)',
          }}>
            {PHASE_LABELS[phase]}
          </span>
        </div>

        {/* Progress % */}
        <span style={{
          fontSize:   10.5,
          color:      'rgba(255,255,255,0.22)',
          fontFamily: 'var(--font-mono)',
        }}>
          {Math.round(progress * 100)}%
        </span>
      </div>

      {/* ── Progress bar ──────────────────────────────────────────────────── */}
      <div style={{
        height:       2,
        background:   'rgba(255,255,255,0.05)',
        borderRadius: 99,
        overflow:     'hidden',
      }}>
        <motion.div
          animate={{ width: `${Math.round(progress * 100)}%` }}
          transition={{ duration: 0.55, ease: 'easeOut' }}
          style={{
            height:       '100%',
            background:   `linear-gradient(90deg, ${color}55, ${color})`,
            borderRadius: 99,
          }}
        />
      </div>

      {/* ── Checkpoints ───────────────────────────────────────────────────── */}
      {checkpoints.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
          <AnimatePresence initial={false}>
            {checkpoints.slice(-6).map(cp => (
              <motion.div
                key={cp.id}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.22, ease: 'easeOut' }}
                style={{
                  display:    'flex',
                  alignItems: 'flex-start',
                  gap:        7,
                  fontSize:   12,
                  fontFamily: 'var(--font-ui)',
                  color:      cp.status === 'done'
                    ? 'rgba(52,211,153,0.70)'
                    : 'rgba(255,255,255,0.48)',
                  lineHeight: 1.5,
                }}
              >
                <span style={{
                  flexShrink: 0,
                  marginTop:  2,
                  fontSize:   10,
                  color:      cp.status === 'done' ? '#34d399' : `${color}cc`,
                  fontWeight: 700,
                }}>
                  {cp.status === 'done' ? '✔' : '→'}
                </span>
                <span>{cp.label}</span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* ── Live streaming agent text ──────────────────────────────────────── */}
      <LiveTextArea color={color} />
    </motion.div>
  );
}
