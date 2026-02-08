/**
 * AtomsAgentTimeline - Passive Agent Timeline
 * Read-only. Zero authority. No buttons. No clicks.
 * UI observes. Agent acts.
 */

import { useIDEStore } from "@/stores/ide-store";

export function AtomsAgentTimeline() {
    const activityLog = useIDEStore((s) => s.activityLog);

    if (activityLog.length === 0) {
        return (
            <div className="h-full w-full flex items-center justify-center text-sm text-gray-500">
                Agent timeline empty
            </div>
        );
    }

    return (
        <div className="h-full w-full overflow-auto text-sm text-gray-300">
            {activityLog.map((e) => (
                <div
                    key={e.id}
                    className="px-3 py-1.5 border-b border-neutral-800 flex items-start gap-2"
                >
                    <span className="opacity-50 text-xs shrink-0">
                        {new Date(e.timestamp).toLocaleTimeString()}
                    </span>
                    <span className={e.success === false ? "text-red-400" : e.success === true ? "text-green-400" : ""}>
                        {e.action}
                    </span>
                    {e.detail && (
                        <span className="opacity-50 truncate">{e.detail}</span>
                    )}
                </div>
            ))}
        </div>
    );
}
