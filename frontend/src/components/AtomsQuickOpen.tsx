/**
 * Atoms keyboard shortcuts — Cmd/Ctrl+P (file switch), Cmd/Ctrl+Shift+P (command palette)
 * Minimal overlay, no UI pollution.
 */

import React, { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/utils';

export type QuickOpenMode = 'file' | 'command';

interface FileItem {
  path: string;
  name: string;
}

interface CommandItem {
  id: string;
  label: string;
  run: () => void;
}

interface AtomsQuickOpenProps {
  mode: QuickOpenMode;
  onClose: () => void;
  files: FileItem[];
  commands: CommandItem[];
  onOpenFile: (path: string, name: string) => void;
}

export function AtomsQuickOpen({
  mode,
  onClose,
  files,
  commands,
  onOpenFile,
}: AtomsQuickOpenProps) {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const isFile = mode === 'file';
  const filteredFiles = isFile
    ? files.filter((f) => f.path.toLowerCase().includes(query.toLowerCase()) || f.name.toLowerCase().includes(query.toLowerCase()))
    : [];
  const filteredCommands = !isFile
    ? commands.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()))
    : [];
  const fileCount = filteredFiles.length;
  const commandCount = filteredCommands.length;
  const itemCount = isFile ? fileCount : commandCount;
  const maxSelected = Math.max(0, itemCount - 1);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    setSelected(0);
  }, [query]);

  useEffect(() => {
    listRef.current?.querySelector(`[data-index="${selected}"]`)?.scrollIntoView({ block: 'nearest' });
  }, [selected]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelected((s) => (s >= maxSelected ? 0 : s + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelected((s) => (s <= 0 ? maxSelected : s - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (isFile && filteredFiles[selected]) {
        const f = filteredFiles[selected];
        onOpenFile(f.path, f.name);
        onClose();
      } else if (!isFile && filteredCommands[selected]) {
        filteredCommands[selected].run();
        onClose();
      }
    }
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-[560px] rounded overflow-hidden animate-scale-in"
        style={{
          background: '#252526',
          border: '1px solid #3c3c3c',
          boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 px-3 py-2" style={{ borderBottom: '1px solid #3c3c3c' }}>
          <span className="text-[13px] text-[#9a9a9a]">{isFile ? 'Go to file' : '>'}</span>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isFile ? '' : 'Type a command...'}
            className="flex-1 bg-transparent outline-none text-[13px] text-[#e5e5e5] placeholder:text-[#6b6b6b]"
          />
        </div>
        <div
          ref={listRef}
          className="max-h-[320px] overflow-y-auto py-1"
          style={{ background: '#252526' }}
        >
          {isFile
            ? filteredFiles.map((f, i) => (
                <div
                  key={f.path}
                  data-index={i}
                  className={cn(
                    'px-3 py-1.5 text-[13px] cursor-pointer transition-colors duration-150',
                    i === selected ? 'bg-[#094771] text-white' : 'text-[#e5e5e5] hover:bg-[#2a2d2e]'
                  )}
                  onClick={() => {
                    onOpenFile(f.path, f.name);
                    onClose();
                  }}
                >
                  {f.path}
                </div>
              ))
            : filteredCommands.map((c, i) => (
                <div
                  key={c.id}
                  data-index={i}
                  className={cn(
                    'px-3 py-1.5 text-[13px] cursor-pointer transition-colors duration-150',
                    i === selected ? 'bg-[#094771] text-white' : 'text-[#e5e5e5] hover:bg-[#2a2d2e]'
                  )}
                  onClick={() => {
                    c.run();
                    onClose();
                  }}
                >
                  {c.label}
                </div>
              ))}
          {itemCount === 0 && (
            <div className="px-3 py-4 text-[13px] text-[#6b6b6b]">
              {isFile ? 'No files found' : 'No commands found'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
