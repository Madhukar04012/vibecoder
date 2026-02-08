/**
 * Pill-style mode switcher: Editor ↔ App Viewer
 * Segmented control, not tabs. IDE-grade, minimal.
 */

import React from 'react';
import { FileCode, Monitor } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ViewMode = 'editor' | 'viewer' | 'terminal';

interface ModeSwitcherProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
  className?: string;
}

export function ModeSwitcher({ mode, onChange, className }: ModeSwitcherProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-0.5 rounded-full bg-[#2d2d30] p-0.5 border border-white/[0.06]',
        className
      )}
    >
      <button
        type="button"
        onClick={() => onChange('editor')}
        className={cn(
          'flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[13px] transition-all duration-200',
          mode === 'editor'
            ? 'bg-[#2d2d30] text-white'
            : 'text-[#858585] hover:text-[#d4d4d4] hover:bg-white/5 hover:scale-[1.02] active:scale-[0.98]'
        )}
      >
        <FileCode className="w-3.5 h-3.5 shrink-0" />
        <span>Editor</span>
      </button>
      <button
        type="button"
        onClick={() => onChange('viewer')}
        className={cn(
          'flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[13px] transition-all duration-200',
          mode === 'viewer'
            ? 'bg-[#2d2d30] text-white'
            : 'text-[#858585] hover:text-[#d4d4d4] hover:bg-white/5 hover:scale-[1.02] active:scale-[0.98]'
        )}
      >
        <Monitor className="w-3.5 h-3.5 shrink-0" />
        <span>App Viewer</span>
      </button>
    </div>
  );
}
