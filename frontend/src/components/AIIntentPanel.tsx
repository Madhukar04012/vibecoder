/**
 * AI Intent Panel — shows what AI intends to do BEFORE changes
 * Controlled autonomy: user approves, edits scope, or cancels
 */

import React from 'react';
import { X, Check, FileText, FileEdit, Play, FolderPlus, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useIDEStore, type AIIntentAction } from '@/stores/ide-store';

const actionIcons: Record<AIIntentAction['type'], React.ReactNode> = {
  read: <FileText className="w-4 h-4 text-[#7eb8da]" />,
  modify: <FileEdit className="w-4 h-4 text-[#c586c0]" />,
  run: <Play className="w-4 h-4 text-[#4fc3f7]" />,
  create: <FolderPlus className="w-4 h-4 text-[#81c784]" />,
  delete: <Trash2 className="w-4 h-4 text-[#f87171]" />,
};

export function AIIntentPanel() {
  const {
    pendingIntent,
    showIntentPanel,
    dismissIntent,
    approveIntent,
    rejectIntent,
  } = useIDEStore();

  if (!showIntentPanel || !pendingIntent) return null;

  return (
    <div className="absolute inset-0 z-50 flex items-end justify-center pointer-events-none">
      <div className="pointer-events-auto w-full max-w-lg mx-4 mb-4 bg-[#252526] border border-[#3c3c3c] rounded-lg shadow-2xl overflow-hidden animate-slide-up">
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#3c3c3c] bg-[#2d2d30]">
          <h3 className="text-sm font-medium text-white">AI intends to:</h3>
          <button
            onClick={dismissIntent}
            className="p-1.5 rounded text-[#858585] hover:text-white hover:bg-white/10 transition-all duration-200 hover:scale-110 active:scale-95"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="px-4 py-3 space-y-2 max-h-48 overflow-y-auto">
          {pendingIntent.actions.map((a, i) => (
            <div
              key={i}
              className="flex items-center gap-2 text-sm text-[#d4d4d4] animate-fade-in"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <span className="text-[#81c784]">✓</span>
              {actionIcons[a.type]}
              <span className="capitalize">{a.type}:</span>
              <span className="text-[#4fc3f7] truncate">{a.target}</span>
              {a.detail && (
                <span className="text-[#858585] text-xs truncate">{a.detail}</span>
              )}
            </div>
          ))}
        </div>
        {pendingIntent.scope && (
          <div className="px-4 py-2 border-t border-[#3c3c3c] text-xs text-[#858585]">
            <span className="font-medium">Scope:</span> {pendingIntent.scope}
          </div>
        )}
        <div className="flex gap-2 px-4 py-3 border-t border-[#3c3c3c] bg-[#2d2d30]">
          <button
            onClick={approveIntent}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-[#0e639c] hover:bg-[#1177bb] text-white text-sm font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
          >
            <Check className="w-4 h-4" />
            Approve
          </button>
          <button
            onClick={() => {}}
            className="px-4 py-2 rounded-lg bg-[#3c3c3c] hover:bg-[#4c4c4c] text-[#d4d4d4] text-sm transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
          >
            Edit Scope
          </button>
          <button
            onClick={rejectIntent}
            className="px-4 py-2 rounded-lg bg-[#3c3c3c] hover:bg-red-500/20 text-[#f87171] text-sm transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
