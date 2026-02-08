/**
 * AtomsAgentTimelineOverlay - Floating Agent Timeline
 * Shows AI activity log as a floating overlay
 */

import { useIDEStore, type AIActivityEntry } from "@/stores/ide-store";
import { Sparkles, FileCode, MessageSquare, AlertCircle, X } from "lucide-react";

interface Props {
  onClose: () => void;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  file_create: <FileCode size={12} className="text-emerald-400" />,
  thinking: <Sparkles size={12} className="text-blue-400" />,
  message: <MessageSquare size={12} className="text-gray-400" />,
  error: <AlertCircle size={12} className="text-red-400" />,
};

export function AtomsAgentTimelineOverlay({ onClose }: Props) {
  const activityLog = useIDEStore((s) => s.activityLog);

  return (
    <div
      className="fixed right-4 bottom-4 w-[380px] max-h-[50vh] bg-[#111] border border-[#222] rounded-xl shadow-2xl overflow-hidden z-50 flex flex-col"
      role="dialog"
      aria-label="Agent Timeline"
    >
      <div className="flex items-center justify-between px-3 py-2 border-b border-[#1e1e1e] shrink-0">
        <div className="flex items-center gap-2">
          <Sparkles size={12} className="text-blue-400" />
          <span className="text-[12px] text-gray-300 font-medium">Activity Log</span>
          <span className="text-[10px] text-gray-600">{activityLog.length}</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md hover:bg-[#2a2a2a] text-gray-500 hover:text-gray-300 transition-colors"
          aria-label="Close"
        >
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-auto text-[12px]">
        {activityLog.length === 0 ? (
          <div className="px-3 py-8 text-gray-600 text-center">No activity yet</div>
        ) : (
          [...activityLog].reverse().map((e) => (
            <div
              key={e.id}
              className="px-3 py-2 border-b border-[#1a1a1a] flex items-start gap-2 hover:bg-[#1a1a1a] transition-colors"
            >
              <div className="mt-0.5 shrink-0">
                {TYPE_ICONS[e.type || 'message'] || <Sparkles size={12} className="text-gray-500" />}
              </div>
              <div className="flex-1 min-w-0">
                <span className={
                  e.success === false ? "text-red-400" :
                  e.success === true ? "text-emerald-400" : "text-gray-300"
                }>
                  {e.action}
                </span>
                {e.detail && (
                  <span className="block text-[11px] text-gray-600 truncate mt-0.5">{e.detail}</span>
                )}
              </div>
              <span className="text-[10px] text-gray-600 shrink-0">
                {new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
