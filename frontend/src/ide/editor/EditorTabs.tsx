'use client';

import { X } from 'lucide-react';
import { useIDE } from '@/src/ide/store';
import { cn } from '@/lib/utils';

// Helper to get icon based on extension (simplified)
const FileIcon = ({ path }: { path: string }) => {
    if (path.endsWith('.tsx') || path.endsWith('.ts')) return <span className="text-blue-400">TS</span>;
    if (path.endsWith('.py')) return <span className="text-yellow-400">PY</span>;
    if (path.endsWith('.json')) return <span className="text-yellow-200">{ }</span>;
    return <span className="text-slate-400">TXT</span>;
};

export function EditorTabs() {
    const { openFiles, activeFile, setActiveFile, closeFile, locked } = useIDE();

    if (openFiles.length === 0) return null;

    return (
        <div className="flex w-full items-center border-b border-white/10 bg-slate-950/50">
            {openFiles.map((file: string) => {
                const isActive = file === activeFile;
                const fileName = file.split('/').pop() || file;

                return (
                    <div
                        key={file}
                        className={cn(
                            'group flex min-w-[120px] max-w-[200px] items-center gap-2 border-r border-white/5 px-3 py-2 text-xs transition-colors',
                            isActive ? 'bg-slate-900 text-slate-100' : 'bg-transparent text-slate-500 hover:bg-slate-900/30',
                            locked && 'cursor-not-allowed opacity-50'
                        )}
                    >
                        <button
                            type="button"
                            onClick={() => !locked && setActiveFile(file)}
                            className="flex min-w-0 flex-1 items-center gap-2"
                            disabled={locked}
                            aria-label={`Open ${fileName}`}
                        >
                            <div className="scale-75">
                                <FileIcon path={file} />
                            </div>
                            <span className="min-w-0 flex-1 truncate text-left">{fileName}</span>
                        </button>
                        <button
                            type="button"
                            onClick={(e) => {
                                e.stopPropagation();
                                if (!locked) closeFile(file);
                            }}
                            aria-label={`Close ${fileName}`}
                            className={cn(
                                'rounded-sm opacity-0 hover:bg-white/10 group-hover:opacity-100',
                                isActive && 'opacity-100'
                            )}
                            disabled={locked}
                        >
                            <X className="h-3 w-3" />
                        </button>
                    </div>
                );
            })}
        </div>
    );
}
