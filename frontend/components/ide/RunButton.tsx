'use client';

import { Play, Square } from 'lucide-react';
import { useIDEStore } from '@/store/ideStore';
import { Button } from '@/components/ui/button';

export function RunButton() {
    const isExecuting = useIDEStore((state) => state.isExecuting);
    const runState = useIDEStore((state) => state.runState);
    const executeRun = useIDEStore((state) => state.executeRun);
    const abortExecution = useIDEStore((state) => state.abortExecution);

    const handleClick = () => {
        if (isExecuting) {
            abortExecution();
        } else {
            executeRun();
        }
    };

    // Status label for the button
    const statusLabel =
        runState === 'compiling'
            ? 'Compiling...'
            : runState === 'testing'
                ? 'Testing...'
                : runState === 'success'
                    ? 'Success'
                    : runState === 'error'
                        ? 'Failed'
                        : 'Run';

    return (
        <Button
            onClick={handleClick}
            variant={runState === 'error' ? 'outline' : 'primary'}
            size="sm"
            className="gap-2"
            aria-label={isExecuting ? 'Stop execution' : 'Run project'}
        >
            {isExecuting ? <Square className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
            <span>{statusLabel}</span>
        </Button>
    );
}
