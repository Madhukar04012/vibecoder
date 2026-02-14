import React, { useRef, useEffect } from 'react';
import { useTerminalStore } from '@/stores/terminalStore';
import { cn } from '@/lib/utils';

export const Terminal: React.FC = () => {
    const terminals = useTerminalStore((state) => state.terminals);
    const activeTerminalId = useTerminalStore((state) => state.activeTerminalId);
    const addOutput = useTerminalStore((state) => state.addOutput);
    const bottomRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const activeTerminal = terminals.find((t) => t.id === activeTerminalId);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [activeTerminal?.output]);

    const handleCommand = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && activeTerminalId) {
            const command = e.currentTarget.value;
            if (command.trim()) {
                addOutput(activeTerminalId, `$ ${command}`);
                addOutput(activeTerminalId, `Command executed: ${command}`);
                e.currentTarget.value = '';
            }
        }
    };

    if (!activeTerminal) {
        return (
            <div className="flex items-center justify-center h-full bg-[#1E1E1E] text-[#858585]">
                <p className="text-sm">No terminal active</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-[#1E1E1E] font-mono text-sm">
            <div className="flex-1 overflow-y-auto p-3 text-[#89D185]">
                {activeTerminal.output.map((line, index) => (
                    <div key={index} className="whitespace-pre-wrap">
                        {line}
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
            <div className="flex items-center px-3 py-2 border-t border-[#3E3E42]">
                <span className="text-[#89D185] mr-2">$</span>
                <input
                    ref={inputRef}
                    type="text"
                    className="flex-1 bg-transparent text-[#CCCCCC] outline-none"
                    placeholder="Type a command..."
                    onKeyDown={handleCommand}
                    autoFocus
                />
            </div>
        </div>
    );
};