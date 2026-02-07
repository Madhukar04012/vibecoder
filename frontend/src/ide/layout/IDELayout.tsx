'use client';

import { Play, Square } from 'lucide-react';
import { useIDE } from '@/src/ide/store';
import { MonacoEditor } from '@/src/ide/editor/Editor';
import { EditorTabs } from '@/src/ide/editor/EditorTabs';
import { Console } from '@/src/ide/console/Console';
import { FileTree } from '@/src/ide/files/FileTree';
import { CommandChat } from '@/src/ide/chat/CommandChat';
import { StatusBar } from '@/src/ide/status/StatusBar';

export function IDELayout() {
    const { mode, run, reset, currentUser } = useIDE();
    const isRunning = mode === 'running';

    return (
        <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
            {/* Top bar with Run button */}
            <div className="flex h-12 items-center justify-between border-b border-white/10 bg-slate-900 px-4">
                <div className="flex items-center gap-3">
                    <h1 className="text-sm font-semibold">VibeCober IDE</h1>
                    {currentUser?.email && (
                        <div className="text-xs text-slate-300">
                            <span className="text-slate-400">Signed in as</span> {currentUser.name ? `${currentUser.name} (${currentUser.email})` : currentUser.email}
                        </div>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    <button
                        disabled={isRunning}
                        onClick={run}
                        className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${isRunning
                            ? 'cursor-not-allowed bg-slate-700 text-slate-400'
                            : mode === 'error'
                                ? 'bg-red-500 text-white hover:bg-red-600'
                                : 'bg-violet-600 text-white hover:bg-violet-700'
                            }`}
                    >
                        {isRunning ? <Square className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                        <span>{isRunning ? 'Running…' : mode === 'error' ? 'Failed' : 'Run'}</span>
                    </button>
                    {mode === 'error' && (
                        <button
                            onClick={reset}
                            className="rounded-lg bg-slate-700 px-3 py-1.5 text-sm font-medium text-slate-300 hover:bg-slate-600"
                        >
                            Reset
                        </button>
                    )}
                </div>
            </div>

            {/* Main layout */}
            <div className="flex flex-1 overflow-hidden">
                {/* Left: Files + Chat */}
                <div className="flex w-64 flex-col border-r border-white/10">
                    {/* File tree */}
                    <div className="flex-1 overflow-auto border-b border-white/10">
                        <div className="border-b border-white/10 bg-slate-900 px-3 py-2">
                            <p className="text-[11px] font-medium text-slate-400">FILES</p>
                        </div>
                        <div className="p-2">
                            <FileTree />
                        </div>
                    </div>

                    {/* Command chat */}
                    <div className="h-48 border-t border-white/10">
                        <div className="border-b border-white/10 bg-slate-900 px-3 py-2">
                            <p className="text-[11px] font-medium text-slate-400">COMMANDS</p>
                        </div>
                        <CommandChat />
                    </div>
                </div>

                {/* Right: Editor + Console */}
                <div className="flex flex-1 flex-col overflow-hidden">
                    {/* Editor Tabs + Editor */}
                    <div className="flex flex-1 flex-col border-b border-white/10 bg-slate-950">
                        <EditorTabs />
                        <div className="flex-1 relative">
                            <MonacoEditor />
                        </div>
                    </div>

                    {/* Console */}
                    <div className="h-48 shrink-0 border-t border-white/10">
                        <div className="border-b border-white/10 bg-slate-900 px-3 py-2">
                            <p className="text-[11px] font-medium text-slate-400">CONSOLE</p>
                        </div>
                        <Console />
                    </div>
                </div>
            </div>

            {/* Bottom: Status bar */}
            <StatusBar />
        </div>
    );
}
