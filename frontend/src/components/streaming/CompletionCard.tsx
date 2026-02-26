/**
 * CompletionCard — Final state after pipeline completes.
 *
 * Rendered below PhaseBlock when phase === 'completed'.
 * Replaces the DoneBanner in simple mode.
 * Does NOT auto-reset — stays visible for the user to see.
 */

import { motion } from 'framer-motion';
import { CheckCircle2, FolderOpen } from 'lucide-react';
import { useStreamStore } from '@/streaming/stream-store';

export function CompletionCard() {
  const fileBatches = useStreamStore(s => s.fileBatches);
  const totalFiles  = fileBatches.reduce((acc, b) => acc + b.files.length, 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut', delay: 0.15 }}
      style={{
        margin:        '6px 20px 20px',
        background:    'rgba(52,211,153,0.05)',
        border:        '1px solid rgba(52,211,153,0.18)',
        borderRadius:  14,
        padding:       '18px 20px',
      }}
    >
      {/* Header */}
      <div style={{
        display:      'flex',
        alignItems:   'center',
        gap:          10,
        marginBottom: totalFiles > 0 ? 10 : 0,
      }}>
        <CheckCircle2 size={15} style={{ color: '#34d399', flexShrink: 0 }} />
        <span style={{
          fontSize:   14,
          fontWeight: 700,
          color:      '#34d399',
          fontFamily: 'var(--font-ui)',
        }}>
          Project Successfully Generated
        </span>
      </div>

      {/* File count row */}
      {totalFiles > 0 && (
        <div style={{
          display:    'flex',
          alignItems: 'center',
          gap:        7,
          fontSize:   12.5,
          color:      'rgba(255,255,255,0.40)',
          fontFamily: 'var(--font-ui)',
        }}>
          <FolderOpen size={12} style={{ flexShrink: 0, opacity: 0.6 }} />
          <span>
            {totalFiles} file{totalFiles !== 1 ? 's' : ''} generated
          </span>
        </div>
      )}

      {/* Subtext */}
      <p style={{
        fontSize:   12.5,
        color:      'rgba(255,255,255,0.38)',
        fontFamily: 'var(--font-ui)',
        lineHeight: 1.65,
        margin:     '10px 0 0',
      }}>
        Your AI engineering team has completed the build. Open the files panel to explore the generated project.
      </p>
    </motion.div>
  );
}
