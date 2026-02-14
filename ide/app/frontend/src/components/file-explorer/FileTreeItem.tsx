import React, { useState } from 'react';
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from 'lucide-react';
import { cn } from '@/lib/utils';
import { FileNode } from '@/types';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { useEditorStore } from '@/stores/editorStore';

interface FileTreeItemProps {
    node: FileNode;
    level: number;
}

export const FileTreeItem: React.FC<FileTreeItemProps> = ({ node, level }) => {
    const [isHovered, setIsHovered] = useState(false);
    const toggleFolder = useWorkspaceStore((state) => state.toggleFolder);
    const openTab = useEditorStore((state) => state.openTab);

    const handleClick = () => {
        if (node.type === 'folder') {
            toggleFolder(node.path);
        } else {
            openTab(node.id, node.name, node.path, node.content || '', node.language || 'plaintext');
        }
    };

    const getFileIcon = () => {
        if (node.type === 'folder') {
            return node.isOpen ? (
                <FolderOpen className="w-4 h-4 text-[#DDB100]" />
            ) : (
                <Folder className="w-4 h-4 text-[#DDB100]" />
            );
        }

        const ext = node.name.split('.').pop()?.toLowerCase();
        const colors: Record<string, string> = {
            tsx: 'text-[#007ACC]',
            ts: 'text-[#007ACC]',
            jsx: 'text-[#61DAFB]',
            js: 'text-[#F7DF1E]',
            json: 'text-[#89D185]',
            md: 'text-[#858585]',
            css: 'text-[#264DE4]',
            html: 'text-[#E34C26]',
        };

        return <File className={cn('w-4 h-4', colors[ext || ''] || 'text-[#858585]')} />;
    };

    return (
        <div>
            <div
                className={cn(
                    'flex items-center gap-1 py-0.5 px-2 cursor-pointer hover:bg-[#2A2D2E] text-[#CCCCCC] text-sm group',
                    isHovered && 'bg-[#2A2D2E]'
                )}
                style={{ paddingLeft: `${level * 12 + 8}px` }}
                onClick={handleClick}
                onMouseEnter={() => setIsHovered(true)}
                onMouseLeave={() => setIsHovered(false)}
            >
                {node.type === 'folder' && (
                    <span className="w-4 h-4 flex items-center justify-center">
                        {node.isOpen ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                        )}
                    </span>
                )}
                {node.type === 'file' && <span className="w-4" />}
                {getFileIcon()}
                <span className="flex-1 truncate">{node.name}</span>
                {node.modified && <span className="w-1.5 h-1.5 rounded-full bg-[#007ACC]" />}
            </div>
            {node.type === 'folder' && node.isOpen && node.children && (
                <div>
                    {node.children.map((child) => (
                        <FileTreeItem key={child.id} node={child} level={level + 1} />
                    ))}
                </div>
            )}
        </div>
    );
};