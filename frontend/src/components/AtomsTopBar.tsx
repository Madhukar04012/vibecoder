/**
 * AtomsTopBar - ATMOS Mode: Indicator-Only Top Bar
 * 
 * ATMOS Rules:
 * - NO Run button (AI runs everything)
 * - NO Share button
 * - View tabs are indicators only (switch view, don't trigger execution)
 * - Shows ATMOS phase badge instead of AI status
 */

import { Code2, Globe } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAtmosStore, PHASE_DISPLAY } from "@/lib/atmos-state";
import AccountHoverPanel from "./AccountHoverPanel";
import { useState } from "react";

export type TopBarActiveView = "editor" | "app";

export function AtomsTopBar({
  view,
  setView,
  projectName,
}: {
  view: "editor" | "app";
  setView: (v: "editor" | "app") => void;
  projectName?: string | null;
}) {
  const [accountOpen, setAccountOpen] = useState(false);
  const phase = useAtmosStore((s) => s.phase);
  const statusMessage = useAtmosStore((s) => s.statusMessage);

  const phaseInfo = PHASE_DISPLAY[phase];

  const views: { id: TopBarActiveView; label: string; icon: React.ReactNode }[] = [
    { id: "editor", label: "Code", icon: <Code2 size={14} /> },
    { id: "app", label: "Preview", icon: <Globe size={14} /> },
  ];

  return (
    <header
      className="w-full flex items-center h-[42px] border-b text-[12px] select-none"
      style={{ background: "var(--ide-topbar-bg)", borderColor: "var(--ide-border)", color: "var(--ide-text)" }}
    >
      {/* LEFT: App Icon + Project Info */}
      <div className="flex items-center gap-2 pl-2">

        {/* APP / ACCOUNT ICON */}
        <div
          className="relative"
          onMouseEnter={() => setAccountOpen(true)}
          onMouseLeave={() => setAccountOpen(false)}
        >
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-600 to-purple-700 flex items-center justify-center cursor-pointer text-white font-bold hover:scale-105 transition-transform shadow-md shadow-purple-500/20">
            ⚛
          </div>
          {accountOpen && <AccountHoverPanel />}
        </div>

        {/* Project Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md" style={{ background: 'var(--ide-surface-hover)', border: '1px solid var(--ide-border)' }}>
          <div
            className="w-2 h-2 rounded-full transition-colors"
            style={{ backgroundColor: phaseInfo.color }}
          />
          <span className="font-medium truncate max-w-[160px]" style={{ color: 'var(--ide-text-secondary)' }}>
            {projectName || "New Project"}
          </span>
        </div>

        {/* ATMOS Phase Badge */}
        {phase !== 'idle' && (
          <div
            className="flex items-center gap-1.5 px-2 py-1 rounded-md border text-[11px]"
            style={{
              backgroundColor: `${phaseInfo.color}15`,
              borderColor: `${phaseInfo.color}25`,
              color: phaseInfo.color,
            }}
          >
            {phase !== 'live' && (
              <div
                className="w-1.5 h-1.5 rounded-full animate-pulse"
                style={{ backgroundColor: phaseInfo.color }}
              />
            )}
            <span className="font-medium">
              {statusMessage || phaseInfo.label}
            </span>
          </div>
        )}
      </div>

      {/* CENTER: View Switcher (indicators only — do NOT trigger execution) */}
      <div className="flex-1 flex items-center justify-center">
        <div className="flex items-center h-[28px] rounded-lg overflow-hidden" style={{ background: 'var(--ide-surface-hover)', border: '1px solid var(--ide-border)' }}>
          {views.map((v) => (
            <button
              key={v.id}
              onClick={() => setView(v.id)}
              className={cn(
                "flex items-center gap-1.5 px-3 h-full text-[12px] transition-all duration-150",
              )}
              style={{
                background: view === v.id ? 'var(--ide-settings-sidebar)' : 'transparent',
                color: view === v.id ? 'var(--ide-text)' : 'var(--ide-text-muted)',
              }}
            >
              {v.icon}
              <span>{v.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* RIGHT: Empty — no Run, no Share (ATMOS mode) */}
      <div className="w-[60px]" />
    </header>
  );
}
