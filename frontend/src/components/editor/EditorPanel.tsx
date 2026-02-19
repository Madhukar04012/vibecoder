/**
 * EditorPanel - Main editor area with tabs, code editor, and terminal
 */

import { useState } from "react";
import { EditorTabs } from "./EditorTabs";
import { EditorCanvas } from "./EditorCanvas";
import { TerminalPanel } from "./TerminalPanel";
import { useIDEStore } from "@/stores/ide-store";

interface EditorPanelProps {
  isSplit?: boolean;
}

export function EditorPanel({ isSplit = false }: EditorPanelProps) {
  const openFiles = useIDEStore((s) => s.openFiles);
  const activeFile = useIDEStore((s) => s.activeFile);
  const [rightFile] = useState<string | null>(null);
  const [terminalCollapsed, setTerminalCollapsed] = useState(false);

  const effectiveRightFile = (() => {
    if (rightFile && openFiles.includes(rightFile)) return rightFile;
    const other = openFiles.find(f => f !== activeFile);
    return other ?? activeFile;
  })();

  return (
    <div className="flex flex-col h-full min-h-0 min-w-0 overflow-hidden">
      <EditorTabs />
      <div className="flex flex-col flex-1 min-h-0 min-w-0 overflow-hidden">
        {/* Editor area */}
        <div className="flex flex-1 min-h-0 min-w-0 overflow-hidden">
          <div className={`flex flex-col min-h-0 min-w-0 overflow-hidden relative ${isSplit ? "flex-1" : "flex-1"}`} style={{ 
            position: 'relative', 
            height: '100%', 
            width: '100%',
            background: 'var(--ide-bg)',
            boxShadow: '0 1px 2px rgba(0,0,0,0.04)'
          }}>
            <EditorCanvas />
          </div>
          {isSplit && (
            <div className="flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden">
              <EditorCanvas file={effectiveRightFile} />
            </div>
          )}
        </div>

        {/* Terminal panel */}
        <div style={{ height: terminalCollapsed ? 30 : 180, minHeight: terminalCollapsed ? 30 : 100 }} className="shrink-0">
          <TerminalPanel
            collapsed={terminalCollapsed}
            onToggle={() => setTerminalCollapsed((c) => !c)}
          />
        </div>
      </div>
    </div>
  );
}
