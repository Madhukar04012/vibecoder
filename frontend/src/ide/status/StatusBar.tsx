'use client';

import { useIDE } from '@/src/ide/store';
import { cn } from '@/lib/utils';

export function StatusBar() {
    const { mode, cloudEnabled, dbConnected, githubConnected, gitStatus, gitChanges, syncGit } = useIDE();

    return (
        <div className="flex items-center gap-4 border-t border-white/10 bg-slate-950 px-3 py-1.5 text-[11px] text-slate-400">
            <div className="flex items-center gap-1.5">
                <div className={`h-1.5 w-1.5 rounded-full transition-colors ${!cloudEnabled ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                <span>Local</span>
            </div>
            <div className="flex items-center gap-1.5">
                <div className={`h-1.5 w-1.5 rounded-full transition-colors ${cloudEnabled ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                <span>{cloudEnabled ? 'Cloud Active' : 'Cloud Disabled'}</span>
            </div>
            <div className="flex items-center gap-1.5">
                <div className={`h-1.5 w-1.5 rounded-full transition-colors ${dbConnected ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                <span>DB</span>
            </div>
            <button
                onClick={() => syncGit()}
                disabled={!githubConnected || gitStatus === 'clean' || gitStatus === 'syncing'}
                className={`flex items-center gap-1.5 transition-colors hover:text-slate-200 ${!githubConnected ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
                    }`}
            >
                <div className={cn(
                    "h-1.5 w-1.5 rounded-full transition-colors",
                    githubConnected && gitStatus === 'clean' && "bg-emerald-400",
                    githubConnected && gitStatus === 'modified' && "bg-blue-400",
                    githubConnected && gitStatus === 'syncing' && "bg-yellow-400 animate-pulse",
                    !githubConnected && "bg-slate-600"
                )} />
                <span>
                    {gitStatus === 'syncing' ? 'Syncing...' :
                        gitStatus === 'modified' ? `${gitChanges} Changes (Click to Sync)` :
                            githubConnected ? 'Git Synced' : 'No Git'}
                </span>
            </button>
            <div className="ml-auto flex items-center gap-1.5">
                <div
                    className={`h-1.5 w-1.5 rounded-full ${mode === 'running' ? 'bg-blue-400' : mode === 'error' ? 'bg-red-400' : 'bg-slate-600'
                        }`}
                />
                <span>{mode === 'running' ? 'Running' : mode === 'error' ? 'Error' : 'Idle'}</span>
            </div>
        </div>
    );
}
