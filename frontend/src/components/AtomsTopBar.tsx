/**
 * AtomsTopBar - IDE top bar with view switching and project controls
 */

import { useState } from "react";
import {
  Code2, Globe, Terminal, Share2, Play, Sparkles,
  PanelLeftClose, PanelLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useIDEStore } from "@/stores/ide-store";

export type TopBarActiveView = "editor" | "app" | "terminal";

export function AtomsTopBar({
  view,
  setView,
  sidebarVisible,
  onToggleSidebar,
  onPublish,
  projectName,
}: {
  view: "editor" | "app" | "terminal";
  setView: (v: "editor" | "app" | "terminal") => void;
  sidebarVisible?: boolean;
  onToggleSidebar?: () => void;
  onPublish?: () => void;
  projectName?: string | null;
}) {
  const aiStatus = useIDEStore((s) => s.aiStatus);
  const aiFileProgress = useIDEStore((s) => s.aiFileProgress);
  const fileCount = useIDEStore((s) => Object.keys(s.fileContents).length);

  const views: { id: TopBarActiveView; label: string; icon: React.ReactNode }[] = [
    { id: "editor", label: "Code", icon: <Code2 size={14} /> },
    { id: "app", label: "Preview", icon: <Globe size={14} /> },
    { id: "terminal", label: "Shell", icon: <Terminal size={14} /> },
  ];

  return (
    <header
      className="w-full flex items-center h-[42px] border-b text-[12px] select-none"
      style={{ background: "#111", borderColor: "#1e1e1e", color: "#e5e5e5" }}
    >
      {/* LEFT: Toggle + Project */}
      <div className="flex items-center gap-1.5 pl-2">
        <button
          onClick={onToggleSidebar}
          className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-[#1e1e1e] text-gray-400 hover:text-gray-200 transition-colors"
          title={sidebarVisible ? "Hide sidebar" : "Show sidebar"}
        >
          {sidebarVisible ? <PanelLeftClose size={15} /> : <PanelLeft size={15} />}
        </button>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#1a1a1a] border border-[#222]">
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="text-gray-300 font-medium truncate max-w-[160px]">
            {projectName || "New Project"}
          </span>
          {fileCount > 0 && (
            <span className="text-[10px] text-gray-600 ml-1">{fileCount} files</span>
          )}
        </div>

        {/* AI Status */}
        {aiStatus !== 'idle' && aiStatus !== 'done' && (
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-blue-500/10 border border-blue-500/15 text-blue-300 text-[11px]">
            <Sparkles size={10} className="animate-pulse" />
            {aiStatus === 'thinking' && "Thinking..."}
            {aiStatus === 'generating' && `Generating ${aiFileProgress.current}/${aiFileProgress.total}`}
            {aiStatus === 'streaming' && "Writing..."}
          </div>
        )}
      </div>

      {/* CENTER: View Switcher */}
      <div className="flex-1 flex items-center justify-center">
        <div className="flex items-center h-[28px] rounded-lg bg-[#1a1a1a] border border-[#222] overflow-hidden">
          {views.map((v) => (
            <button
              key={v.id}
              onClick={() => setView(v.id)}
              className={cn(
                "flex items-center gap-1.5 px-3 h-full text-[12px] transition-all duration-150",
                view === v.id
                  ? "bg-[#2a2a2a] text-white"
                  : "text-gray-500 hover:text-gray-300 hover:bg-[#1e1e1e]",
              )}
            >
              {v.icon}
              <span>{v.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* RIGHT: Actions */}
      <div className="flex items-center gap-1.5 pr-3">
        <button
          onClick={onPublish}
          className="flex items-center gap-1.5 h-[28px] px-3 rounded-lg bg-emerald-600/15 border border-emerald-500/20 text-emerald-300 hover:bg-emerald-600/25 transition-colors text-[12px]"
        >
          <Play size={12} />
          Run
        </button>
        <button className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-[#1e1e1e] text-gray-500 hover:text-gray-300 transition-colors" title="Share">
          <Share2 size={14} />
        </button>
      </div>
    </header>
  );
}
