'use client';

import { useState, useRef, useEffect } from 'react';
import { useIDE } from '@/src/ide/store';
import { cn } from '@/lib/utils';

interface LogEntry {
    type: 'user' | 'system' | 'info' | 'success' | 'error';
    content: string;
}

export function CommandChat() {
    const {
        toggleCloud, toggleDB, toggleGitHub,
        cloudEnabled, dbConnected, githubConnected,
        mode
    } = useIDE();

    const [input, setInput] = useState('');
    const [logs, setLogs] = useState<LogEntry[]>([
        { type: 'info', content: 'VibeCober Command Surface ready.' },
        { type: 'info', content: 'Type "help" for available commands.' },
    ]);

    const bottomRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const handleCommand = async (cmd: string) => {
        const command = cmd.trim().toLowerCase();
        if (!command) return;

        // Add user command to log
        setLogs(prev => [...prev, { type: 'user', content: command }]);
        setInput('');

        // Simulate thinking delay
        await new Promise(r => setTimeout(r, 400));

        switch (true) {
            case command === 'help':
                setLogs(prev => [...prev, {
                    type: 'system',
                    content: 'Available commands:\n  enable cloud    - Connect to Atoms Cloud\n  connect db      - Provision PostgreSQL database\n  link github     - Connect GitHub repository\n  status          - Show current infrastructure\n  clear           - Clear console'
                }]);
                break;

            case command === 'clear':
                setLogs([]);
                break;

            case command === 'status':
                setLogs(prev => [...prev, {
                    type: 'info',
                    content: `Infrastructure Status:\n  Cloud: ${cloudEnabled ? 'Enabled' : 'Disabled'}\n  Database: ${dbConnected ? 'Connected' : 'Disconnected'}\n  GitHub: ${githubConnected ? 'Linked' : 'Disconnected'}`
                }]);
                break;

            case command.includes('enable cloud'):
                setLogs(prev => [...prev, { type: 'system', content: 'Provisioning Atoms Cloud environment...' }]);
                await new Promise(r => setTimeout(r, 1200));
                toggleCloud(true);
                setLogs(prev => [...prev, { type: 'success', content: '✓ Cloud environment active' }]);
                break;

            case command.includes('connect db'):
                if (!cloudEnabled) {
                    setLogs(prev => [...prev, { type: 'error', content: 'Error: Cloud must be enabled first. Type "enable cloud".' }]);
                    break;
                }
                setLogs(prev => [...prev, { type: 'system', content: 'Spinning up PostgreSQL instance...' }]);
                await new Promise(r => setTimeout(r, 1500));
                toggleDB(true);
                setLogs(prev => [...prev, { type: 'success', content: '✓ Database connected (postgres:15)' }]);
                break;

            case command.includes('link github'):
                setLogs(prev => [...prev, { type: 'system', content: 'Authenticating with GitHub...' }]);
                await new Promise(r => setTimeout(r, 1000));
                toggleGitHub(true);
                setLogs(prev => [...prev, { type: 'success', content: '✓ Repository linked' }]);
                break;

            default:
                setLogs(prev => [...prev, { type: 'error', content: `Unknown command: "${command}"` }]);
        }
    };

    return (
        <div className="flex h-full flex-col bg-slate-950 font-mono text-xs">
            <div className="flex-1 overflow-auto p-3 space-y-1">
                {logs.map((log, i) => (
                    <div key={i} className={cn(
                        "whitespace-pre-wrap",
                        log.type === 'user' && "text-slate-100 font-bold mt-2 before:content-['>_'] before:mr-2 before:text-slate-500",
                        log.type === 'system' && "text-slate-400 pl-4",
                        log.type === 'info' && "text-blue-400 pl-4",
                        log.type === 'success' && "text-emerald-400 pl-4",
                        log.type === 'error' && "text-red-400 pl-4",
                    )}>
                        {log.content}
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>

            <div className="flex items-center border-t border-white/10 bg-slate-900/50 p-2">
                <span className="mr-2 text-slate-500">{'>'}</span>
                <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleCommand(input)}
                    className="flex-1 bg-transparent text-slate-200 outline-none placeholder:text-slate-600"
                    placeholder="Type a command..."
                    autoFocus
                    disabled={mode === 'running'}
                />
            </div>
        </div>
    );
}
