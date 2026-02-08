import { useState } from "react";
import {
  Monitor,
  Globe,
  Terminal,
  TerminalSquare,
  Share2,
} from "lucide-react";

export type TopBarActiveView = "editor" | "app" | "terminal";

export function AtomsTopBar({
  view,
  setView,
  sidebarVisible,
  onToggleSidebar,
  terminalVisible,
  onToggleTerminal,
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
  // Active nav: whichever was last clicked shows icon+name pill; others show icon only
  const [activeView, setActiveView] = useState<TopBarActiveView>("editor");

  const handleSetView = (v: "editor" | "app") => {
    setActiveView(v);
    setView(v);
  };

  const handleTerminalClick = () => {
    setActiveView("terminal");
    setView("terminal");
  };

  return (
    <header
      className="atoms-header w-full flex items-center border-b text-[13px] [&_svg]:opacity-70 [&_button:hover_svg]:opacity-100"
      style={{
        background: "var(--atoms-charcoal)",
        borderColor: "#2f2f2f",
        color: "var(--atoms-pearl-white)",
      }}
    >
      {/* LEFT: Project info button */}
      <div className="flex items-center gap-2">
        <button className="h-9 pl-3 pr-4 rounded-lg bg-[#1f1f1f] hover:bg-[#262626] flex items-center gap-2 max-w-[240px] min-w-[180px] transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]">
          <Globe size={16} className="text-[#e5e5e5] shrink-0" />
          <Monitor size={14} className="text-[#e5e5e5] shrink-0" />
          <span className="truncate text-[#e5e5e5]">
            {projectName ? `${projectName}${projectName.length > 18 ? '…' : ''}` : 'No project'}
          </span>
        </button>
      </div>

      {/* MIDDLE: Nav items – active shows icon+name (pill), inactive icon-only (circle) */}
      <div className="flex-1 flex items-center justify-center gap-1 ml-6">
        {/* App Viewer */}
        {activeView === "app" ? (
          <button
            onClick={() => handleSetView("app")}
            className="h-9 pl-3 pr-4 rounded-lg flex items-center gap-2 bg-[#3a3a3a] transition-all duration-200"
          >
            <Monitor size={16} className="shrink-0" />
            <span>App Viewer</span>
          </button>
        ) : (
          <button
            onClick={() => handleSetView("app")}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-[#333333] transition-all duration-200 hover:scale-110 active:scale-95"
            aria-label="App Viewer"
          >
            <Monitor size={16} />
          </button>
        )}

        {/* Editor */}
        {activeView === "editor" ? (
          <button
            onClick={() => handleSetView("editor")}
            className="h-9 pl-3 pr-4 rounded-lg flex items-center gap-2 bg-[#3a3a3a] transition-all duration-200"
          >
            <Terminal size={16} className="shrink-0" />
            <span>Editor</span>
          </button>
        ) : (
          <button
            onClick={() => handleSetView("editor")}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-[#333333] transition-all duration-200 hover:scale-110 active:scale-95"
            aria-label="Editor"
          >
            <Terminal size={16} />
          </button>
        )}

        {/* Terminal */}
        {activeView === "terminal" ? (
          <button
            onClick={handleTerminalClick}
            className="h-9 pl-3 pr-4 rounded-lg flex items-center gap-2 bg-[#3a3a3a] transition-all duration-200"
          >
            <TerminalSquare size={16} className="shrink-0" />
            <span>Terminal</span>
          </button>
        ) : (
          <button
            onClick={handleTerminalClick}
            className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-[#333333] transition-all duration-200 hover:scale-110 active:scale-95"
            aria-label="Terminal"
          >
            <TerminalSquare size={16} />
          </button>
        )}
      </div>

      {/* RIGHT: Share, Publish */}
      <div className="flex items-center gap-2">
        <button className="w-8 h-8 rounded-full hover:bg-[#333333] flex items-center justify-center transition-all duration-200 hover:scale-110 active:scale-95" aria-label="Share">
          <Share2 size={16} />
        </button>
        <button
          onClick={onPublish}
          className="h-[28px] px-4 rounded-lg bg-[#2563eb] hover:bg-[#1d4ed8] text-white font-medium transition-all duration-200 hover:scale-[1.03] active:scale-[0.97]"
        >
          Publish
        </button>
      </div>
    </header>
  );
}
