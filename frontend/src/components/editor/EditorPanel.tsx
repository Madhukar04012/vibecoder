/**
 * EditorPanel - Main editor area with tabs and split view
 */

import { useState } from "react";
import { EditorTabs } from "./EditorTabs";
import { EditorCanvas } from "./EditorCanvas";
import { useIDEStore } from "@/stores/ide-store";

interface EditorPanelProps {
  isSplit?: boolean;
}

export function EditorPanel({ isSplit = false }: EditorPanelProps) {
  const openFiles = useIDEStore((s) => s.openFiles);
  const activeFile = useIDEStore((s) => s.activeFile);
  const [rightFile] = useState<string | null>(null);

  const effectiveRightFile = (() => {
    if (rightFile && openFiles.includes(rightFile)) return rightFile;
    const other = openFiles.find(f => f !== activeFile);
    return other ?? activeFile;
  })();

  return (
    <div className="flex flex-col flex-1 min-h-0 min-w-0 overflow-hidden">
      <EditorTabs />
      <div className="flex flex-1 min-h-0 min-w-0 overflow-hidden">
        <div className={`flex flex-col min-h-0 min-w-0 overflow-hidden ${isSplit ? "flex-1 border-r border-[#1e1e1e]" : "flex-1"}`}>
          <EditorCanvas />
        </div>
        {isSplit && (
          <div className="flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden">
            <EditorCanvas file={effectiveRightFile} />
          </div>
        )}
      </div>
    </div>
  );
}
