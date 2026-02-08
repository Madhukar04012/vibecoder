/**
 * Diff Review Panel — Phase 4.3
 * Renders DiffPlan as reviewable per-file diffs. No filesystem writes.
 *
 * Phase 4.3 invariants:
 * - Diff preview never mutates filesystem
 * - Preview content is computed in memory only
 * - Approve is the only path to diff application (Phase 4.4)
 */

import React, { useState } from 'react';
import { X, Check, FileCode } from 'lucide-react';
import { DiffEditor } from '@monaco-editor/react';
import { useIDEStore } from '@/stores/ide-store';
import { applyDiffActionsInMemory } from '@/lib/diff';

function getLanguage(filePath: string): string {
  const ext = filePath.split('.').pop()?.toLowerCase() ?? '';
  const map: Record<string, string> = {
    ts: 'typescript',
    tsx: 'typescript',
    js: 'javascript',
    jsx: 'javascript',
    json: 'json',
    css: 'css',
    html: 'html',
    py: 'python',
    md: 'markdown',
  };
  return map[ext] ?? 'plaintext';
}

interface DiffReviewPanelProps {
  onApproveDiff?: (diffPlan: import('@/lib/diff').DiffPlan) => void | Promise<void>;
}

export function DiffReviewPanel({ onApproveDiff }: DiffReviewPanelProps) {
  const {
    pendingDiffPlan,
    diffReviewFiles,
    dismissDiffReview,
    rejectDiffReview,
  } = useIDEStore();

  const [activeFile, setActiveFile] = useState<string>('');

  if (!pendingDiffPlan || pendingDiffPlan.diffs.length === 0) return null;

  const affectedFiles = [...new Set(pendingDiffPlan.diffs.map((d) => d.file))].filter(
    (f) => diffReviewFiles[f] !== undefined
  );

  if (affectedFiles.length === 0) return null;

  const currentFile = activeFile || affectedFiles[0];
  const original = diffReviewFiles[currentFile] ?? '';
  const preview = applyDiffActionsInMemory(original, pendingDiffPlan.diffs, currentFile);

  return (
    <div className="absolute inset-0 z-50 flex flex-col bg-[#1e1e1e]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#3c3c3c] bg-[#2d2d30] shrink-0">
        <div className="flex items-center gap-3">
          <FileCode className="w-5 h-5 text-[#4fc3f7]" />
          <div>
            <h3 className="text-sm font-medium text-white">Diff Review</h3>
            <p className="text-xs text-[#858585] truncate max-w-md">{pendingDiffPlan.summary}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={dismissDiffReview}
            className="p-1.5 rounded text-[#858585] hover:text-white hover:bg-white/10 transition-all duration-200 hover:scale-110 active:scale-95"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
          <button
            onClick={rejectDiffReview}
            className="px-4 py-2 rounded-lg bg-[#3c3c3c] hover:bg-red-500/20 text-[#f87171] text-sm transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
          >
            Reject
          </button>
          <button
            onClick={async () => {
              if (onApproveDiff && pendingDiffPlan) {
                await onApproveDiff(pendingDiffPlan);
              } else {
                useIDEStore.getState().approveDiffReview();
              }
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0e639c] hover:bg-[#1177bb] text-white text-sm font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
          >
            <Check className="w-4 h-4" />
            Approve
          </button>
        </div>
      </div>

      <div className="flex border-b border-[#3c3c3c] bg-[#252526] shrink-0 overflow-x-auto">
        {affectedFiles.map((path) => (
          <button
            key={path}
            onClick={() => setActiveFile(path)}
            className={`px-4 py-2 text-sm whitespace-nowrap border-b-2 transition-all duration-200 rounded-t-sm ${
              (activeFile || affectedFiles[0]) === path
                ? 'border-[#0e639c] text-white'
                : 'border-transparent text-[#858585] hover:text-[#d4d4d4] hover:bg-white/5'
            }`}
          >
            {path.split('/').pop() ?? path}
          </button>
        ))}
      </div>

      <div className="flex-1 min-h-0">
        <DiffEditor
          height="100%"
          language={getLanguage(currentFile)}
          original={original}
          modified={preview}
          theme="vs-dark"
          options={{
            readOnly: true,
            renderSideBySide: true,
            diffWordWrap: 'on',
            scrollBeyondLastLine: false,
          }}
        />
      </div>
    </div>
  );
}
