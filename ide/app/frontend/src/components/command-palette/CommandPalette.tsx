import React, { useState, useEffect } from 'react';
import { Search, File, GitBranch, Settings, Terminal as TerminalIcon } from 'lucide-react';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { useUIStore } from '@/stores/uiStore';
import { useEditorStore } from '@/stores/editorStore';
import { useWorkspaceStore } from '@/stores/workspaceStore';
import { cn } from '@/lib/utils';

interface Command {
    id: string;
    label: string;
    icon: React.ReactNode;
    action: () => void;
    category: string;
}

export const CommandPalette: React.FC = () => {
    const commandPaletteOpen = useUIStore((state) => state.commandPaletteOpen);
    const toggleCommandPalette = useUIStore((state) => state.toggleCommandPalette);
    const setActiveView = useUIStore((state) => state.setActiveView);
    const toggleBottomPanel = useUIStore((state) => state.toggleBottomPanel);
    const files = useWorkspaceStore((state) => state.files);
    const openTab = useEditorStore((state) => state.openTab);
    const [search, setSearch] = useState('');
    const [selectedIndex, setSelectedIndex] = useState(0);

    const getAllFiles = (nodes: any[]): any[] => {
        let result: any[] = [];
        for (const node of nodes) {
            if (node.type === 'file') {
                result.push(node);
            }
            if (node.children) {
                result = result.concat(getAllFiles(node.children));
            }
        }
        return result;
    };

    const allFiles = getAllFiles(files);

    const commands: Command[] = [
        {
            id: 'explorer',
            label: 'View: Show Explorer',
            icon: <File className="w-4 h-4" />,
            action: () => {
                setActiveView('explorer');
                toggleCommandPalette();
            },
            category: 'View',
        },
        {
            id: 'git',
            label: 'View: Show Source Control',
            icon: <GitBranch className="w-4 h-4" />,
            action: () => {
                setActiveView('git');
                toggleCommandPalette();
            },
            category: 'View',
        },
        {
            id: 'terminal',
            label: 'View: Toggle Terminal',
            icon: <TerminalIcon className="w-4 h-4" />,
            action: () => {
                toggleBottomPanel();
                toggleCommandPalette();
            },
            category: 'View',
        },
        {
            id: 'settings',
            label: 'Preferences: Open Settings',
            icon: <Settings className="w-4 h-4" />,
            action: () => {
                setActiveView('settings');
                toggleCommandPalette();
            },
            category: 'Preferences',
        },
        ...allFiles.map((file) => ({
            id: `file-${file.id}`,
            label: `Open: ${file.path}`,
            icon: <File className="w-4 h-4" />,
            action: () => {
                openTab(file.id, file.name, file.path, file.content || '', file.language || 'plaintext');
                toggleCommandPalette();
            },
            category: 'Files',
        })),
    ];

    const filteredCommands = commands.filter((cmd) =>
        cmd.label.toLowerCase().includes(search.toLowerCase())
    );

    useEffect(() => {
        setSelectedIndex(0);
    }, [search]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex((prev) => (prev + 1) % filteredCommands.length);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % filteredCommands.length);
        } else if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
            e.preventDefault();
            filteredCommands[selectedIndex].action();
        }
    };

    return (
        <Dialog open={commandPaletteOpen} onOpenChange={toggleCommandPalette}>
            <DialogContent className="bg-[#252526] border-[#3E3E42] p-0 max-w-2xl">
                <div className="flex items-center gap-2 px-4 py-3 border-b border-[#3E3E42]">
                    <Search className="w-4 h-4 text-[#858585]" />
                    <Input
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type a command or search..."
                        className="flex-1 bg-transparent border-0 text-[#CCCCCC] focus-visible:ring-0 focus-visible:ring-offset-0"
                        autoFocus
                    />
                </div>
                <div className="max-h-[400px] overflow-y-auto">
                    {filteredCommands.length === 0 ? (
                        <div className="py-8 text-center text-[#858585] text-sm">
                            No commands found
                        </div>
                    ) : (
                        filteredCommands.map((cmd, index) => (
                            <div
                                key={cmd.id}
                                onClick={cmd.action}
                                className={cn(
                                    'flex items-center gap-3 px-4 py-2 cursor-pointer transition-colors',
                                    index === selectedIndex
                                        ? 'bg-[#007ACC] text-white'
                                        : 'text-[#CCCCCC] hover:bg-[#2A2D2E]'
                                )}
                            >
                                {cmd.icon}
                                <div className="flex-1">
                                    <div className="text-sm">{cmd.label}</div>
                                    <div
                                        className={cn(
                                            'text-xs',
                                            index === selectedIndex ? 'text-white/70' : 'text-[#858585]'
                                        )}
                                    >
                                        {cmd.category}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
};