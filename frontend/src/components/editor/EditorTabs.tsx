/**
 * EditorTabs - Professional file tabs with modern design
 */

import { useIDEStore } from "@/stores/ide-store";
import { X, Sparkles, FileCode, FileJson, FileText, Hash, Braces, File } from "lucide-react";
import { cn } from "@/lib/utils";

const FILE_TYPES: Record<string, { icon: typeof File; color: string; label: string }> = {
  ts: { icon: FileCode, color: "#3178c6", label: "TS" },
  tsx: { icon: FileCode, color: "#3178c6", label: "TSX" },
  js: { icon: FileCode, color: "#f7df1e", label: "JS" },
  jsx: { icon: FileCode, color: "#f7df1e", label: "JSX" },
  py: { icon: FileCode, color: "#3776ab", label: "PY" },
  json: { icon: FileJson, color: "#f59e0b", label: "JSON" },
  css: { icon: Hash, color: "#06b6d4", label: "CSS" },
  html: { icon: Braces, color: "#f97316", label: "HTML" },
  md: { icon: FileText, color: "#6b7280", label: "MD" },
  txt: { icon: FileText, color: "#6b7280", label: "TXT" },
};

function getFileConfig(path: string) {
  const ext = path.split(".").pop()?.toLowerCase() || "";
  return FILE_TYPES[ext] || { icon: File, color: "#6b7280", label: "FILE" };
}

export function EditorTabs() {
  const openFiles = useIDEStore((s) => s.openFiles);
  const activeFile = useIDEStore((s) => s.activeFile);
  const setActiveFile = useIDEStore((s) => s.setActiveFile);
  const closeFile = useIDEStore((s) => s.closeFile);
  const fileStatuses = useIDEStore((s) => s.fileStatuses);
  const fileLiveWriting = useIDEStore((s) => s.fileLiveWriting);

  if (openFiles.length === 0) return null;

  return (
    <div 
      className="flex items-center h-[42px] overflow-x-auto scrollbar-none gap-1 px-2" 
      style={{ background: 'var(--ide-surface)', borderBottom: '1px solid var(--ide-border)' }}
    >
      {openFiles.map((file) => {
        const name = file.split("/").pop() || file;
        const isActive = activeFile === file;
        const status = fileStatuses[file];
        const config = getFileConfig(file);
        const IconComp = config.icon;
        const isModified = status?.isModified;
        const isAI = status?.isAIGenerated;
        const isLiveWriting = fileLiveWriting[file];

        return (
          <div
            key={file}
            className={cn(
              "flex items-center gap-2 px-3 h-[32px] text-[13px] cursor-pointer select-none transition-all duration-200 group relative rounded-lg",
              isActive && "shadow-sm",
              isLiveWriting && "animate-pulse"
            )}
            style={{
              background: isActive ? 'var(--ide-bg)' : 'transparent',
              color: isActive ? 'var(--ide-text)' : 'var(--ide-text-muted)',
              fontWeight: isActive ? 500 : 400,
              border: isActive ? '1px solid var(--ide-border)' : '1px solid transparent',
            }}
            onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'var(--ide-surface-hover)'; }}
            onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
            onClick={() => setActiveFile(file)}
          >
            {/* File icon */}
            <IconComp size={14} style={{ color: config.color }} className="shrink-0" />

            {/* Name */}
            <span className="truncate max-w-[140px]">{name}</span>

            {/* Status indicators */}
            <div className="flex items-center gap-1.5 ml-1">
              {/* Live writing indicator */}
              {isLiveWriting && (
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                </div>
              )}

              {/* AI indicator */}
              {isAI && !isModified && !isLiveWriting && (
                <Sparkles size={12} className="text-blue-400 shrink-0" />
              )}

              {/* Modified indicator */}
              {isModified && (
                <div className="w-2 h-2 rounded-full bg-amber-400 shrink-0" />
              )}
            </div>

            {/* Close button */}
            <button
              className={cn(
                "p-1 rounded-md transition-all ml-1",
                isActive ? "opacity-60 hover:opacity-100" : "opacity-0 group-hover:opacity-60 hover:!opacity-100"
              )}
              style={{ color: 'var(--ide-text-muted)' }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--ide-surface-hover)'; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
              onClick={(e) => { e.stopPropagation(); closeFile(file); }}
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
