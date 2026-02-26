/**
 * ModeToggle — Simple / Developer / Debug mode switcher.
 *
 * Simple:    curated summaries, thinking blocks, completions
 * Developer: + file trees, tool calls, all event cards
 * Debug:     + raw event types, timestamps
 */

import { useStreamStore, type StreamMode } from '@/streaming/stream-store';

const MODES: Array<{ id: StreamMode; label: string; tip: string }> = [
  { id: 'simple',    label: 'Simple', tip: 'Curated summaries only' },
  { id: 'developer', label: 'Dev',    tip: 'File trees + tool calls' },
  { id: 'debug',     label: 'Debug',  tip: 'Raw event stream' },
];

export function ModeToggle() {
  const mode    = useStreamStore(s => s.mode);
  const setMode = useStreamStore(s => s.setMode);

  return (
    <div
      role="group"
      aria-label="Streaming mode"
      style={{
        display:    'flex',
        alignItems: 'center',
        gap:        1,
        padding:    2,
        borderRadius: 8,
        background: 'rgba(255,255,255,0.04)',
        border:     '1px solid rgba(255,255,255,0.08)',
      }}
    >
      {MODES.map(({ id, label, tip }) => {
        const active = mode === id;
        return (
          <button
            key={id}
            type="button"
            title={tip}
            onClick={() => setMode(id)}
            style={{
              padding:       '3px 9px',
              borderRadius:  6,
              fontSize:      10.5,
              fontWeight:    active ? 600 : 400,
              fontFamily:    'var(--font-ui)',
              background:    active ? 'rgba(255,255,255,0.10)' : 'transparent',
              color:         active ? 'rgba(255,255,255,0.82)' : 'rgba(255,255,255,0.32)',
              border:        'none',
              cursor:        'pointer',
              letterSpacing: '0.01em',
              transition:    'all 0.15s ease',
              userSelect:    'none',
            }}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
