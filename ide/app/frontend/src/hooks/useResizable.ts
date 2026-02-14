import { useState, useCallback, useEffect, useRef } from 'react';

interface UseResizableOptions {
    initialSize: number;
    minSize: number;
    maxSize: number;
    onResize?: (size: number) => void;
}

export const useResizable = ({ initialSize, minSize, maxSize, onResize }: UseResizableOptions) => {
    const [size, setSize] = useState(initialSize);
    const [isResizing, setIsResizing] = useState(false);
    const startPosRef = useRef(0);
    const startSizeRef = useRef(initialSize);

    const handleMouseDown = useCallback((e: React.MouseEvent) => {
        e.preventDefault();
        setIsResizing(true);
        startPosRef.current = e.clientX;
        startSizeRef.current = size;
    }, [size]);

    useEffect(() => {
        if (!isResizing) return;

        const handleMouseMove = (e: MouseEvent) => {
            const delta = e.clientX - startPosRef.current;
            const newSize = Math.max(minSize, Math.min(maxSize, startSizeRef.current + delta));
            setSize(newSize);
            onResize?.(newSize);
        };

        const handleMouseUp = () => {
            setIsResizing(false);
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isResizing, minSize, maxSize, onResize]);

    return { size, isResizing, handleMouseDown };
};