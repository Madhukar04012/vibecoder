/**
 * TerminalPanel — Professional Terminal Output
 * Shows build output, logs, and command execution results.
 */

import { useEffect, useRef } from "react";
import { Terminal, ChevronUp, Circle, Trash2 } from "lucide-react";
import { useIDEStore, type TerminalLine } from "@/stores/ide-store";
import { cn } from "@/lib/utils";

interface TerminalPanelProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

function colorForType(type: TerminalLine["type"]): string {
  switch (type) {
    case "command": return "#60a5fa";   // blue
    case "stderr":  return "#f87171";   // red
    case "stdout":
    default:        return "#a1a1aa";   // gray
  }
}

export function TerminalPanel({ collapsed = false, onToggle }: TerminalPanelProps) {
  const terminalLines = useIDEStore((s) => s.terminalLines);
  const clearTerminal = useIDEStore((s) => s.clearTerminal);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new lines arrive
  useEffect(() => {
    if (scrollRef.current && !collapsed) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [terminalLines, collapsed]);

  const hasOutput = terminalLines.length > 0;

  return (
    <div
      className="flex flex-col min-w-0 overflow-hidden h-full"
      style={{
        background: "var(--ide-bg-deep)",
        borderTop: "1px solid var(--ide-border)",
      }}
    >
      {/* Header */}
      <div
        className="shrink-0 flex items-center gap-3 px-4 h-[36px] cursor-pointer select-none"
        style={{
          background: "var(--ide-surface)",
          borderBottom: collapsed ? "none" : "1px solid var(--ide-border)",
        }}
        onClick={onToggle}
      >
        <div className="flex items-center gap-2">
          <Terminal size={14} className="text-green-400" />
          <span className="text-[12px] font-semibold uppercase tracking-wider" style={{ color: 'var(--ide-text-muted)' }}>Terminal</span>
        </div>

        {hasOutput && (
          <span className="text-[11px] px-2 py-0.5 rounded-md" style={{ background: 'var(--ide-surface-hover)', color: 'var(--ide-text-muted)' }}>
            {terminalLines.length} lines
          </span>
        )}

        <div className="ml-auto flex items-center gap-2">
          {/* Clear button */}
          {hasOutput && !collapsed && (
            <button
              className="p-1.5 rounded-md transition-colors"
              style={{ color: 'var(--ide-text-muted)' }}
              onClick={(e) => { e.stopPropagation(); clearTerminal(); }}
              title="Clear terminal"
            >
              <Trash2 size={13} />
            </button>
          )}
          
          {/* Collapse toggle */}
          <div className={cn("p-1 rounded transition-transform", !collapsed && "rotate-180")}>
            <ChevronUp size={14} style={{ color: 'var(--ide-text-muted)' }} />
          </div>
        </div>
      </div>

      {/* Terminal output */}
      {!collapsed && (
        <div
          ref={scrollRef}
          className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-4 py-3 font-mono text-[13px] leading-[22px]"
          style={{ background: "var(--ide-bg-deep)" }}
        >
          {terminalLines.length === 0 ? (
            <div className="flex items-center gap-2" style={{ color: 'var(--ide-text-muted)' }}>
              <Circle size={8} className="text-green-500" />
              <span>Terminal ready. Output will appear here...</span>
            </div>
          ) : (
            terminalLines.map((line, i) => (
              <div key={i} className="whitespace-pre-wrap break-all flex items-start gap-2" style={{ color: colorForType(line.type) }}>
                {line.type === "command" ? (
                  <span className="text-green-400 select-none">$</span>
                ) : line.type === "stderr" ? (
                  <span className="text-red-400 select-none text-[10px] font-bold">ERR</span>
                ) : null}
                <span className="flex-1">{line.text}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
