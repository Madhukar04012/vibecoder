'use client';

import { useRef, useEffect } from 'react';
import Editor, { type OnMount } from '@monaco-editor/react';
import { useIDE } from '@/src/ide/store';
import { cn } from '@/lib/utils';
import { getFileContent } from '@/src/ide/files/fileSystem';
import { LSP } from '@/src/ide/lsp';

export function MonacoEditor() {
    const { locked, mode, activeFile } = useIDE();
    const editorRef = useRef<Parameters<OnMount>[0] | null>(null);
    const monacoRef = useRef<Parameters<OnMount>[1] | null>(null);

    const content = activeFile ? getFileContent(activeFile) : '';

    const handleEditorDidMount: OnMount = (editor, monaco) => {
        editorRef.current = editor;
        monacoRef.current = monaco;
    };

    // Trigger LSP validation on content change (simulated via effect since content is prop-driven here)
    useEffect(() => {
        if (!activeFile || !monacoRef.current || !editorRef.current) return;

        const model = editorRef.current.getModel();
        if (!model) return;

        const language = activeFile.endsWith('.py') ? 'python' : 'typescript';

        // Debounce validation
        const timeout = setTimeout(async () => {
            const diagnostics = await LSP.validate(content, language);

            const markers = diagnostics.map((d) => ({
                severity:
                    d.severity === 'error'
                        ? monacoRef.current!.MarkerSeverity.Error
                        : monacoRef.current!.MarkerSeverity.Warning,
                message: d.message,
                startLineNumber: d.startLine,
                startColumn: 1,
                endLineNumber: d.endLine,
                endColumn: 1000,
            }));

            monacoRef.current!.editor.setModelMarkers(model, 'owner', markers);
        }, 500);

        return () => clearTimeout(timeout);
    }, [activeFile, content]);

    if (!activeFile) {
        return (
            <div className="flex h-full items-center justify-center text-slate-500 text-xs">
                Select a file to edit
            </div>
        );
    }

    return (
        <div className={cn('h-full w-full absolute inset-0', mode === 'error' && 'ring-1 ring-inset ring-red-500/30')}>
            <Editor
                height="100%"
                defaultLanguage={activeFile.endsWith('.py') ? 'python' : 'typescript'}
                path={activeFile} // Keep editor state preserved per file
                defaultValue={content}
                value={content} // React controlled mode for hydration
                theme="vs-dark"
                onMount={handleEditorDidMount}
                onChange={() => {
                    // Simple "modification" trigger
                    useIDE.getState().setFileModified();
                }}
                options={{
                    readOnly: locked,
                    minimap: { enabled: false },
                    fontSize: 13,
                    fontFamily: 'JetBrains Mono, monospace',
                    lineHeight: 20,
                    padding: { top: 16 },
                    scrollBeyondLastLine: false,
                    smoothScrolling: true,
                    cursorBlinking: 'smooth',
                    renderLineHighlight: 'none',
                    overviewRulerLanes: 0,
                    hideCursorInOverviewRuler: true,
                    scrollbar: {
                        vertical: 'hidden',
                        horizontal: 'hidden',
                        useShadows: false
                    }
                }}
            />
        </div>
    );
}
