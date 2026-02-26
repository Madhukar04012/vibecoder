/**
 * FileBatchCard — Expandable file tree grouped by directory.
 * Shown in developer + debug modes while files are being generated.
 */

import { useState } from 'react';
import { useStreamStore, type FileBatch } from '@/streaming/stream-store';
import { FolderOpen, ChevronRight, ChevronDown, FileCode } from 'lucide-react';

// ─── Group Row (expandable) ───────────────────────────────────────────────────

function BatchGroup({ batch }: { batch: FileBatch }) {
  const [expanded, setExpanded] = useState(false);
  const { group, files, doneCount } = batch;
  const total   = files.length;
  const pct     = total > 0 ? Math.round((doneCount / total) * 100) : 0;
  const allDone = doneCount >= total && total > 0;
  const groupColor = allDone ? '#34d399' : '#6366f1';

  return (
    <div style={{ marginBottom: 4 }}>
      {/* Group header — click to expand */}
      <button
        type="button"
        onClick={() => setExpanded(e => !e)}
        style={{
          width:          '100%',
          background:     'none',
          border:         'none',
          cursor:         'pointer',
          display:        'flex',
          alignItems:     'center',
          gap:            6,
          padding:        '3px 0',
          textAlign:      'left',
        }}
      >
        {expanded
          ? <ChevronDown  size={10} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          : <ChevronRight size={10} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
        }
        <FolderOpen size={10} style={{ color: groupColor, flexShrink: 0 }} />
        <span style={{
          fontSize:    12,
          fontWeight:  600,
          color:       allDone ? 'rgba(52,211,153,0.80)' : 'rgba(255,255,255,0.65)',
          fontFamily:  'var(--font-ui)',
          flex:        1,
          overflow:    'hidden',
          textOverflow:'ellipsis',
          whiteSpace:  'nowrap',
        }}>
          {group}
        </span>
        <span style={{
          fontSize:    10,
          color:       'var(--text-muted)',
          fontFamily:  'var(--font-mono)',
          flexShrink:  0,
          marginRight: 6,
        }}>
          {doneCount}/{total}
        </span>
        {/* Mini progress strip */}
        <div style={{
          width:        36,
          height:       2,
          borderRadius: 99,
          background:   'rgba(255,255,255,0.08)',
          overflow:     'hidden',
          flexShrink:   0,
        }}>
          <div style={{
            height:     '100%',
            width:      `${pct}%`,
            borderRadius: 99,
            background: allDone
              ? 'linear-gradient(90deg,#34d399,#10b981)'
              : 'linear-gradient(90deg,#6366f1,#818cf8)',
            transition: 'width 0.4s ease',
          }} />
        </div>
      </button>

      {/* Expanded file list */}
      {expanded && (
        <div style={{ paddingLeft: 22, paddingTop: 2 }}>
          {files.map((f, i) => (
            <div
              key={f}
              style={{
                display:    'flex',
                alignItems: 'center',
                gap:        5,
                padding:    '1.5px 0',
                fontSize:   10.5,
                color:      i < doneCount ? 'rgba(52,211,153,0.70)' : 'rgba(255,255,255,0.32)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              <span style={{ color: 'rgba(255,255,255,0.10)', flexShrink: 0 }}>
                {i === files.length - 1 ? '└' : '├'}
              </span>
              <FileCode size={9} style={{ flexShrink: 0, opacity: 0.6 }} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {f.split('/').pop()}
              </span>
              {i < doneCount && (
                <span style={{ marginLeft: 'auto', fontSize: 9, color: '#34d399', flexShrink: 0 }}>✓</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── FileBatchCard ────────────────────────────────────────────────────────────

export function FileBatchCard() {
  const batches = useStreamStore(s => s.fileBatches);
  if (batches.length === 0) return null;

  const totalFiles = batches.reduce((acc, b) => acc + b.files.length, 0);
  const doneFiles  = batches.reduce((acc, b) => acc + b.doneCount, 0);

  return (
    <div className="file-batch-card">
      {/* Header */}
      <div style={{
        display:     'flex',
        alignItems:  'center',
        gap:         8,
        marginBottom: 10,
      }}>
        <span style={{
          fontSize:      10,
          fontWeight:    700,
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          color:         'rgba(99,102,241,0.70)',
          fontFamily:    'var(--font-ui)',
        }}>
          File Tree
        </span>
        <span style={{
          fontSize:   10.5,
          color:      'var(--text-muted)',
          fontFamily: 'var(--font-mono)',
          marginLeft: 'auto',
        }}>
          {doneFiles} / {totalFiles} files
        </span>
      </div>

      {/* Batch groups */}
      {batches.map(b => <BatchGroup key={b.group} batch={b} />)}
    </div>
  );
}
