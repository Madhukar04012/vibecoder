/**
 * EditorTabs - File tabs with status indicators
 * Shows modified/new/AI-generated status
 */

import { useIDEStore } from "@/stores/ide-store";
import { X, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const ICON_MAP: Record<string, { emoji: string; color: string }> = {
  ts: { emoji: "TS", color: "#3178c6" },
  tsx: { emoji: "TX", color: "#3178c6" },
  js: { emoji: "JS", color: "#f7df1e" },
  jsx: { emoji: "JX", color: "#f7df1e" },
  py: { emoji: "PY", color: "#3776ab" },
  json: { emoji: "{}", color: "#6b7280" },
  css: { emoji: "#", color: "#264de4" },
  html: { emoji: "<>", color: "#e34c26" },
  md: { emoji: "MD", color: "#6b7280" },
  txt: { emoji: "TXT", color: "#6b7280" },
};

function getFileIcon(path: string) {
  const ext = path.split(".").pop()?.toLowerCase() || "";
  return ICON_MAP[ext] || { emoji: "F", color: "#6b7280" };
}

export function EditorTabs() {
  const openFiles = useIDEStore((s) => s.openFiles);
  const activeFile = useIDEStore((s) => s.activeFile);
  const setActiveFile = useIDEStore((s) => s.setActiveFile);
  const closeFile = useIDEStore((s) => s.closeFile);
  const fileStatuses = useIDEStore((s) => s.fileStatuses);

  if (openFiles.length === 0) return null;

  return (
    <div className="flex items-center h-[35px] bg-[#111] border-b border-[#1e1e1e] overflow-x-auto scrollbar-none">
      {openFiles.map((file) => {
        const name = file.split("/").pop() || file;
        const isActive = activeFile === file;
        const status = fileStatuses[file];
        const icon = getFileIcon(file);
        const isNew = status?.isNew;
        const isModified = status?.isModified;
        const isAI = status?.isAIGenerated;

        return (
          <div
            key={file}
            className={cn(
              "flex items-center gap-1.5 px-3 h-full text-[12px] cursor-pointer border-r border-[#1a1a1a] select-none transition-colors duration-150 group relative",
              isActive
                ? "bg-[#1a1a1a] text-gray-200"
                : "text-gray-500 hover:text-gray-300 hover:bg-[#151515]",
            )}
            onClick={() => setActiveFile(file)}
          >
            {/* Active indicator */}
            {isActive && (
              <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-blue-500" />
            )}

            {/* File type badge */}
            <span
              className="text-[9px] font-bold px-1 py-0.5 rounded leading-none"
              style={{ background: `${icon.color}22`, color: icon.color }}
            >
              {icon.emoji}
            </span>

            {/* Name */}
            <span className="truncate max-w-[120px]">{name}</span>

            {/* AI indicator */}
            {isAI && !isModified && (
              <Sparkles size={10} className="text-blue-400 shrink-0" />
            )}

            {/* Modified dot */}
            {isModified && (
              <div className="w-2 h-2 rounded-full bg-amber-400 shrink-0" />
            )}

            {/* Close button */}
            <button
              className="p-0.5 rounded opacity-0 group-hover:opacity-100 hover:bg-[#333] transition-all ml-1"
              onClick={(e) => { e.stopPropagation(); closeFile(file); }}
            >
              <X size={12} className="text-gray-500 hover:text-gray-300" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
