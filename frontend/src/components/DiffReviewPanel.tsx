/**
 * DiffReviewPanel — Atmos-style diff review
 * 
 * Shows AI-suggested changes as diffs.
 * User can Apply or Reject each change.
 * AI cannot auto-apply anything.
 */

import { useState, useEffect } from 'react';
import { Check, X, ChevronDown, ChevronRight, FileCode, CheckCircle2, XCircle, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AIDiffManager, type AIDiff, type AIDiffSet } from '@/lib/ai-diff';
import { EventBus, useEventBus } from '@/lib/event-bus';
import { useIDEStore } from '@/stores/ide-store';

// ─── Diff Line Component ────────────────────────────────────────────────────

function DiffLine({ type, content }: { type: 'add' | 'remove' | 'context'; content: string }) {
  return (
    <div className={cn(
      "font-mono text-[12px] px-3 py-0 leading-[1.7] whitespace-pre-wrap",
      type === 'add' && "bg-emerald-500/10 text-emerald-300",
      type === 'remove' && "bg-red-500/10 text-red-300 line-through opacity-60",
      type === 'context' && "text-gray-500",
    )}>
      <span className="inline-block w-4 text-[10px] opacity-50 mr-2 select-none">
        {type === 'add' ? '+' : type === 'remove' ? '-' : ' '}
      </span>
      {content || ' '}
    </div>
  );
}

// ─── Simple Diff View ───────────────────────────────────────────────────────

function SimpleDiffView({ before, after }: { before: string; after: string }) {
  const beforeLines = before.split('\n');
  const afterLines = after.split('\n');

  // For new files, show all as additions
  if (before === '') {
    return (
      <div className="max-h-[300px] overflow-auto border border-[#1e1e1e] rounded-md">
        {afterLines.map((line, i) => (
          <DiffLine key={i} type="add" content={line} />
        ))}
      </div>
    );
  }

  // For modifications, show removed and added
  return (
    <div className="max-h-[300px] overflow-auto border border-[#1e1e1e] rounded-md">
      {beforeLines.map((line, i) => (
        <DiffLine key={`r-${i}`} type="remove" content={line} />
      ))}
      <div className="border-t border-[#222] my-0.5" />
      {afterLines.map((line, i) => (
        <DiffLine key={`a-${i}`} type="add" content={line} />
      ))}
    </div>
  );
}

// ─── Single Diff Card ───────────────────────────────────────────────────────

function DiffCard({ diff, setId }: { diff: AIDiff; setId: string }) {
  const [expanded, setExpanded] = useState(true);
  const openFile = useIDEStore((s) => s.openFile);

  const isNew = diff.before === '';
  const isPending = diff.status === 'pending';

  return (
    <div className={cn(
      "border rounded-lg overflow-hidden transition-all",
      isPending ? "border-blue-500/20 bg-[#0f1219]" : diff.status === 'applied' ? "border-emerald-500/15 bg-emerald-500/5" : "border-red-500/15 bg-red-500/5 opacity-50",
    )}>
      {/* Header */}
      <div
        className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-white/[0.02] transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? <ChevronDown size={12} className="text-gray-500" /> : <ChevronRight size={12} className="text-gray-500" />}
        <FileCode size={13} className={isNew ? "text-emerald-400" : "text-blue-400"} />
        <span className="text-[12px] font-mono text-gray-300 flex-1 truncate">{diff.filePath}</span>
        <span className={cn(
          "text-[10px] px-1.5 py-0.5 rounded-full font-medium",
          isNew ? "bg-emerald-500/15 text-emerald-400" : "bg-blue-500/15 text-blue-400",
        )}>
          {isNew ? 'NEW' : 'MODIFIED'}
        </span>

        {/* Status badge */}
        {diff.status === 'applied' && <CheckCircle2 size={14} className="text-emerald-400" />}
        {diff.status === 'rejected' && <XCircle size={14} className="text-red-400" />}
      </div>

      {/* Diff content */}
      {expanded && (
        <div className="px-3 pb-3">
          <div className="text-[11px] text-gray-500 mb-2 flex items-center gap-1">
            <Sparkles size={10} className="text-blue-400" />
            {diff.agent} — {diff.description}
          </div>

          <SimpleDiffView before={diff.before} after={diff.after} />

          {/* Actions */}
          {isPending && (
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={(e) => { e.stopPropagation(); AIDiffManager.applyDiff(diff.id, setId); openFile(diff.filePath); }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-600/20 border border-emerald-500/25 text-emerald-300 text-[12px] hover:bg-emerald-600/30 transition-colors"
              >
                <Check size={12} /> Apply
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); AIDiffManager.rejectDiff(diff.id, setId); }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-red-600/15 border border-red-500/20 text-red-300 text-[12px] hover:bg-red-600/25 transition-colors"
              >
                <X size={12} /> Reject
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Panel ─────────────────────────────────────────────────────────────

export function DiffReviewPanel() {
  const [diffSets, setDiffSets] = useState<AIDiffSet[]>([]);

  // Listen for new diffs
  useEventBus('AI_DIFF_READY', (event) => {
    setDiffSets((prev) => [...prev, event.payload as AIDiffSet]);
  });

  // Listen for applied/rejected to refresh
  useEventBus('AI_DIFF_APPLIED', () => {
    setDiffSets([...AIDiffManager.getPending()]);
  });

  useEventBus('AI_DIFF_REJECTED', () => {
    setDiffSets([...AIDiffManager.getPending()]);
  });

  // Listen for project reset
  useEventBus('PROJECT_RESET', () => {
    setDiffSets([]);
  });

  if (diffSets.length === 0) {
    return null; // Don't render if no diffs
  }

  return (
    <div className="mx-3 mb-3 space-y-2">
      {diffSets.map((set) => (
        <div key={set.id} className="space-y-2">
          {/* Bulk actions */}
          {set.status === 'reviewing' && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => { AIDiffManager.applyAll(set.id); setDiffSets([...AIDiffManager.getPending()]); }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-600/15 border border-emerald-500/20 text-emerald-300 text-[11px] hover:bg-emerald-600/25 transition-colors"
              >
                <Check size={11} /> Apply All ({set.diffs.filter(d => d.status === 'pending').length})
              </button>
              <button
                onClick={() => { AIDiffManager.rejectAll(set.id); setDiffSets([...AIDiffManager.getPending()]); }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-red-600/10 border border-red-500/15 text-red-300 text-[11px] hover:bg-red-600/20 transition-colors"
              >
                <X size={11} /> Reject All
              </button>
            </div>
          )}

          {/* Individual diffs */}
          {set.diffs.map((diff) => (
            <DiffCard key={diff.id} diff={diff} setId={set.id} />
          ))}
        </div>
      ))}
    </div>
  );
}
