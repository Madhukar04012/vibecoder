import React from 'react';
import { cn } from '@/lib/utils';

interface ResizablePanelProps {
    direction: 'horizontal' | 'vertical';
    size: number;
    onResize: (size: number) => void;
    minSize?: number;
    maxSize?: number;
    children: React.ReactNode;
    className?: string;
}

export const ResizablePanel: React.FC<ResizablePanelProps> = ({
    direction,
    size,
    onResize,
    minSize = 100,
    maxSize = 800,
    children,
    className,
}) => {
    const [isResizing, setIsResizing] = React.useState(false);

    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
        const startPos = direction === 'horizontal' ? e.clientX : e.clientY;
        const startSize = size;

        const handleMouseMove = (moveEvent: MouseEvent) => {
            const currentPos = direction === 'horizontal' ? moveEvent.clientX : moveEvent.clientY;
            const delta = currentPos - startPos;
            const newSize = Math.max(minSize, Math.min(maxSize, startSize + delta));
            onResize(newSize);
        };

        const handleMouseUp = () => {
            setIsResizing(false);
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    };

    const style = direction === 'horizontal' ? { width: size } : { height: size };

    return (
        <div className={cn('relative', className)} style={style}>
            {children}
            <div
                className={cn(
                    'absolute bg-transparent hover:bg-[#007ACC]/30 transition-colors z-50 group',
                    direction === 'horizontal'
                        ? 'right-0 top-0 bottom-0 w-1 cursor-col-resize'
                        : 'bottom-0 left-0 right-0 h-1 cursor-row-resize',
                    isResizing && 'bg-[#007ACC]/50'
                )}
                onMouseDown={handleMouseDown}
            >
                <div
                    className={cn(
                        'absolute bg-[#007ACC] opacity-0 group-hover:opacity-100 transition-opacity',
                        direction === 'horizontal'
                            ? 'right-0 top-1/2 -translate-y-1/2 w-1 h-12 rounded-full'
                            : 'bottom-0 left-1/2 -translate-x-1/2 h-1 w-12 rounded-full',
                        isResizing && 'opacity-100'
                    )}
                />
            </div>
        </div>
    );
};