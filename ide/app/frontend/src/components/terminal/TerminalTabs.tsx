import React from 'react';
import { Plus, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTerminalStore } from '@/stores/terminalStore';
import { Button } from '@/components/ui/button';

export const TerminalTabs: React.FC = () => {
    const terminals = useTerminalStore((state) => state.terminals);
    const activeTerminalId = useTerminalStore((state) => state.activeTerminalId);
    const setActiveTerminal = useTerminalStore((state) => state.setActiveTerminal);
    const closeTerminal = useTerminalStore((state) => state.closeTerminal);
    const createTerminal = useTerminalStore((state) => state.createTerminal);

    return (
        <div className="flex items-center bg-[#252526] border-b border-[#3E3E42] h-[35px]">
            <div className="flex items-center flex-1 overflow-x-auto">
                {terminals.map((terminal) => (
                    <div
                        key={terminal.id}
                        className={cn(
                            'flex items-center gap-2 px-3 py-1.5 border-r border-[#3E3E42] cursor-pointer group',
                            terminal.id === activeTerminalId
                                ? 'bg-[#1E1E1E] text-[#FFFFFF]'
                                : 'text-[#858585] hover:text-[#CCCCCC]'
                        )}
                        onClick={() => setActiveTerminal(terminal.id)}
                    >
                        <span className="text-xs">{terminal.name}</span>
                        {terminals.length > 1 && (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    closeTerminal(terminal.id);
                                }}
                                className="opacity-0 group-hover:opacity-100 hover:bg-[#3E3E42] rounded p-0.5"
                            >
                                <X className="w-3 h-3" />
                            </button>
                        )}
                    </div>
                ))}
            </div>
            <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 mx-2 text-[#858585] hover:text-[#CCCCCC]"
                onClick={() => createTerminal()}
            >
                <Plus className="w-4 h-4" />
            </Button>
        </div>
    );
};