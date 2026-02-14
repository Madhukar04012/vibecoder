import React, { useRef, useEffect } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';
import { useEditorStore } from '@/stores/editorStore';
import { useUIStore } from '@/stores/uiStore';
import * as monaco from 'monaco-editor';

export const MonacoEditor: React.FC = () => {
    const tabs = useEditorStore((state) => state.tabs);
    const activeTabId = useEditorStore((state) => state.activeTabId);
    const updateTabContent = useEditorStore((state) => state.updateTabContent);
    const theme = useUIStore((state) => state.theme);
    const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);

    const activeTab = tabs.find((tab) => tab.id === activeTabId);

    const handleEditorDidMount: OnMount = (editor) => {
        editorRef.current = editor;

        // Configure editor options
        editor.updateOptions({
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Courier New', monospace",
            lineHeight: 20,
            minimap: { enabled: true },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            insertSpaces: true,
            formatOnPaste: true,
            formatOnType: true,
        });
    };

    const handleEditorChange = (value: string | undefined) => {
        if (activeTabId && value !== undefined) {
            updateTabContent(activeTabId, value);
        }
    };

    useEffect(() => {
        if (editorRef.current && activeTab) {
            const model = editorRef.current.getModel();
            if (model && model.getValue() !== activeTab.content) {
                editorRef.current.setValue(activeTab.content);
            }
        }
    }, [activeTab?.id]);

    if (!activeTab) {
        return (
            <div className="flex items-center justify-center h-full bg-[#1E1E1E] text-[#858585]">
                <div className="text-center">
                    <p className="text-lg mb-2">No file open</p>
                    <p className="text-sm">Open a file from the explorer to start editing</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full w-full">
            <Editor
                height="100%"
                language={activeTab.language}
                value={activeTab.content}
                theme={theme === 'dark' ? 'vs-dark' : 'vs-light'}
                onChange={handleEditorChange}
                onMount={handleEditorDidMount}
                options={{
                    readOnly: false,
                    domReadOnly: false,
                }}
            />
        </div>
    );
};