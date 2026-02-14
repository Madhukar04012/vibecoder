import React, { useState } from 'react';
import { GitBranch, Plus, Minus, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useGitStore } from '@/stores/gitStore';
import { cn } from '@/lib/utils';

export const GitPanel: React.FC = () => {
    const changes = useGitStore((state) => state.changes);
    const commits = useGitStore((state) => state.commits);
    const stageChange = useGitStore((state) => state.stageChange);
    const unstageChange = useGitStore((state) => state.unstageChange);
    const commit = useGitStore((state) => state.commit);
    const [commitMessage, setCommitMessage] = useState('');

    const stagedChanges = changes.filter((c) => c.staged);
    const unstagedChanges = changes.filter((c) => !c.staged);

    const handleCommit = () => {
        if (commitMessage.trim() && stagedChanges.length > 0) {
            commit(commitMessage);
            setCommitMessage('');
        }
    };

    const getChangeIcon = (type: string) => {
        const colors = {
            modified: 'text-[#DDB100]',
            added: 'text-[#89D185]',
            deleted: 'text-[#F48771]',
            renamed: 'text-[#007ACC]',
        };
        return colors[type as keyof typeof colors] || 'text-[#858585]';
    };

    return (
        <div className="flex flex-col h-full bg-[#252526]">
            <div className="flex items-center justify-between px-4 py-2 border-b border-[#3E3E42]">
                <span className="text-[#CCCCCC] text-xs font-medium uppercase tracking-wide">
                    Source Control
                </span>
                <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 text-[#858585] hover:text-[#CCCCCC] hover:bg-[#2A2D2E]"
                >
                    <RefreshCw className="w-4 h-4" />
                </Button>
            </div>

            <div className="flex-1 overflow-y-auto">
                {/* Commit Section */}
                <div className="p-3 border-b border-[#3E3E42]">
                    <Input
                        placeholder="Message (Ctrl+Enter to commit)"
                        value={commitMessage}
                        onChange={(e) => setCommitMessage(e.target.value)}
                        className="mb-2 bg-[#3C3C3C] border-[#3E3E42] text-[#CCCCCC] text-sm"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && e.ctrlKey) {
                                handleCommit();
                            }
                        }}
                    />
                    <Button
                        size="sm"
                        className="w-full bg-[#007ACC] hover:bg-[#0098FF] text-white text-xs"
                        onClick={handleCommit}
                        disabled={!commitMessage.trim() || stagedChanges.length === 0}
                    >
                        <GitBranch className="w-3.5 h-3.5 mr-1.5" />
                        Commit ({stagedChanges.length})
                    </Button>
                </div>

                {/* Staged Changes */}
                {stagedChanges.length > 0 && (
                    <div className="border-b border-[#3E3E42]">
                        <div className="px-4 py-2 text-[#CCCCCC] text-xs font-medium uppercase tracking-wide">
                            Staged Changes ({stagedChanges.length})
                        </div>
                        {stagedChanges.map((change) => (
                            <div
                                key={change.path}
                                className="flex items-center justify-between px-4 py-1.5 hover:bg-[#2A2D2E] group"
                            >
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                    <span className={cn('text-xs font-bold', getChangeIcon(change.type))}>
                                        {change.type[0].toUpperCase()}
                                    </span>
                                    <span className="text-[#CCCCCC] text-sm truncate">{change.path}</span>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 text-[#858585] hover:text-[#CCCCCC]"
                                    onClick={() => unstageChange(change.path)}
                                >
                                    <Minus className="w-3.5 h-3.5" />
                                </Button>
                            </div>
                        ))}
                    </div>
                )}

                {/* Unstaged Changes */}
                {unstagedChanges.length > 0 && (
                    <div>
                        <div className="px-4 py-2 text-[#CCCCCC] text-xs font-medium uppercase tracking-wide">
                            Changes ({unstagedChanges.length})
                        </div>
                        {unstagedChanges.map((change) => (
                            <div
                                key={change.path}
                                className="flex items-center justify-between px-4 py-1.5 hover:bg-[#2A2D2E] group"
                            >
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                    <span className={cn('text-xs font-bold', getChangeIcon(change.type))}>
                                        {change.type[0].toUpperCase()}
                                    </span>
                                    <span className="text-[#CCCCCC] text-sm truncate">{change.path}</span>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 text-[#858585] hover:text-[#CCCCCC]"
                                    onClick={() => stageChange(change.path)}
                                >
                                    <Plus className="w-3.5 h-3.5" />
                                </Button>
                            </div>
                        ))}
                    </div>
                )}

                {/* Recent Commits */}
                <div className="border-t border-[#3E3E42] mt-2">
                    <div className="px-4 py-2 text-[#CCCCCC] text-xs font-medium uppercase tracking-wide">
                        Recent Commits
                    </div>
                    {commits.slice(-5).reverse().map((commit) => (
                        <div key={commit.id} className="px-4 py-2 hover:bg-[#2A2D2E]">
                            <div className="text-[#CCCCCC] text-sm">{commit.message}</div>
                            <div className="text-[#858585] text-xs mt-0.5">
                                {commit.author} • {commit.date}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};