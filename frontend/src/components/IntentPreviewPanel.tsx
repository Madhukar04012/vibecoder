/**
 * Intent Preview Panel — Phase 2
 * Shows AI plan BEFORE execution. Human approves or cancels.
 */

import React from 'react';
import { X, Check, FilePlus, FileEdit, Play } from 'lucide-react';
import { useIDEStore, type Plan } from '@/stores/ide-store';

interface IntentPreviewPanelProps {
  onApprovePlan?: (plan: Plan) => void | Promise<void>;
}

export function IntentPreviewPanel({ onApprovePlan }: IntentPreviewPanelProps) {
  const {
    pendingPlan,
    showPlanPanel,
    dismissPlan,
    rejectPlan,
  } = useIDEStore();

  if (!showPlanPanel || !pendingPlan) return null;

  const handleApprove = async () => {
    if (onApprovePlan) {
      await onApprovePlan(pendingPlan);
    } else {
      useIDEStore.getState().approvePlan();
    }
  };

  const { summary, actions } = pendingPlan;
  const createCount = actions.createFiles.length;
  const modifyCount = actions.modifyFiles.length;
  const runCount = actions.runCommands.length;

  return (
    <div className="absolute inset-0 z-50 flex items-end justify-center pointer-events-none">
      <div className="pointer-events-auto w-full max-w-lg mx-4 mb-4 bg-[#252526] border border-[#3c3c3c] rounded-lg shadow-2xl overflow-hidden animate-slide-up">
        <div className="flex items-center justify-between px-4 py-3 border-b border-[#3c3c3c] bg-[#2d2d30]">
          <h3 className="text-sm font-medium text-white">AI Plan</h3>
          <button
            onClick={dismissPlan}
            className="p-1.5 rounded text-[#858585] hover:text-white hover:bg-white/10 transition-all duration-200 hover:scale-110 active:scale-95"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="px-4 py-3 space-y-3 max-h-64 overflow-y-auto">
          <div>
            <p className="text-xs font-medium text-[#858585] mb-1">Summary</p>
            <p className="text-sm text-[#d4d4d4]">&quot;{summary}&quot;</p>
          </div>
          <div>
            <p className="text-xs font-medium text-[#858585] mb-1">Actions</p>
            <ul className="text-sm text-[#d4d4d4] space-y-1">
              {createCount > 0 && (
                <li className="flex items-center gap-2">
                  <FilePlus className="w-4 h-4 text-[#81c784] shrink-0" />
                  Create {createCount} file{createCount !== 1 ? 's' : ''}
                </li>
              )}
              {modifyCount > 0 && (
                <li className="flex items-center gap-2">
                  <FileEdit className="w-4 h-4 text-[#c586c0] shrink-0" />
                  Modify {modifyCount} file{modifyCount !== 1 ? 's' : ''}
                </li>
              )}
              {runCount > 0 && (
                <li className="flex items-center gap-2">
                  <Play className="w-4 h-4 text-[#4fc3f7] shrink-0" />
                  Run: {actions.runCommands.slice(0, 3).join(', ')}
                  {runCount > 3 && ` (+${runCount - 3} more)`}
                </li>
              )}
              {createCount === 0 && modifyCount === 0 && runCount === 0 && (
                <li className="text-[#858585]">No actions</li>
              )}
            </ul>
          </div>
        </div>
        <div className="flex gap-2 px-4 py-3 border-t border-[#3c3c3c] bg-[#2d2d30]">
          <button
            onClick={handleApprove}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-[#0e639c] hover:bg-[#1177bb] text-white text-sm font-medium transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
          >
            <Check className="w-4 h-4" />
            Approve
          </button>
          <button
            onClick={rejectPlan}
            className="px-4 py-2 rounded-lg bg-[#3c3c3c] hover:bg-red-500/20 text-[#f87171] text-sm transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
