import React from 'react';
import { FileTreeItem } from './FileTreeItem';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { Plus, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const FileTree: React.FC = () => {
    const files = useWorkspaceStore((state) => state.files);
    const currentProject = useWorkspaceStore((state) => state.currentProject);

    return (
        <div className="flex flex-col h-full bg-[#252526]">
            <div className="flex items-center justify-between px-4 py-2 border-b border-[#3E3E42]">
                <span className="text-[#CCCCCC] text-xs font-medium uppercase tracking-wide">
                    {currentProject}
                </span>
                <div className="flex items-center gap-1">
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 text-[#858585] hover:text-[#CCCCCC] hover:bg-[#2A2D2E]"
                    >
                        <Plus className="w-4 h-4" />
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 text-[#858585] hover:text-[#CCCCCC] hover:bg-[#2A2D2E]"
                    >
                        <RefreshCw className="w-4 h-4" />
                    </Button>
                </div>
            </div>
            <div className="flex-1 overflow-y-auto py-1">
                {files.map((node) => (
                    <FileTreeItem key={node.id} node={node} level={0} />
                ))}
            </div>
        </div>
    );
};