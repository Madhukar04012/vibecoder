/**
 * Diff Review Editor — collaboration surface when AI proposes edits
 * Left: Current | Right: AI proposal
 * Inline controls: Accept | Reject | Edit then accept
 * Atoms theme + options
 */

import React, { useCallback } from 'react';
import { DiffEditor } from '@monaco-editor/react';
import type * as monaco from 'monaco-editor';
import { Check, X, Pencil } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ATOMS_DARK_THEME, ATOMS_MONACO_OPTIONS } from '@/lib/monaco-atoms-theme';

interface DiffReviewEditorProps {
  filePath: string;
  fileName: string;
  original: string;
  proposed: string;
  language?: string;
  onAccept: () => void;
  onReject: () => void;
  onEditThenAccept: () => void;
  className?: string;
}

export function DiffReviewEditor({
  fileName,
  original,
  proposed,
  language = 'typescript',
  onAccept,
  onReject,
  onEditThenAccept,
  className,
}: DiffReviewEditorProps) {
  const handleBeforeMount = useCallback((monacoInstance: typeof monaco) => {
    monacoInstance.editor.defineTheme('atoms-dark', ATOMS_DARK_THEME as monaco.editor.IStandaloneThemeData);
    monacoInstance.editor.setTheme('atoms-dark');
  }, []);

  return (
    <div className={cn('flex flex-col h-full', className)}>
      <div className="flex items-center justify-between px-3 py-2 shrink-0" style={{ background: '#262626', borderBottom: '1px solid #2f2f2f' }}>
        <span className="text-[13px] text-[#9a9a9a]">
          Reviewing <span className="text-[#4fc3f7]">{fileName}</span>
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={onAccept}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[13px] bg-[#1e3a2f] hover:bg-[#2e4a3f] text-[#81c784]"
          >
            <Check className="w-4 h-4" />
            Accept
          </button>
          <button
            onClick={onReject}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[13px] bg-[#3a1e1e] hover:bg-[#4a2e2e] text-[#f87171]"
          >
            <X className="w-4 h-4" />
            Reject
          </button>
          <button
            onClick={onEditThenAccept}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[13px] bg-[#3a3a3a] hover:bg-[#4a4a4a] text-[#d4d4d4]"
          >
            <Pencil className="w-4 h-4" />
            Edit then accept
          </button>
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <DiffEditor
          height="100%"
          language={language}
          original={original}
          modified={proposed}
          theme="atoms-dark"
          beforeMount={handleBeforeMount}
          options={{
            ...ATOMS_MONACO_OPTIONS,
            readOnly: true,
            renderSideBySide: true,
            diffWordWrap: 'on',
            scrollBeyondLastLine: false,
          }}
        />
      </div>
    </div>
  );
}
