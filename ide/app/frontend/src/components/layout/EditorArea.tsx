import React from 'react';
import { EditorTabs } from '../editor/EditorTabs';
import { MonacoEditor } from '../editor/MonacoEditor';
import { EditorStatusBar } from '../editor/EditorStatusBar';

export const EditorArea: React.FC = () => {
    return (
        <div className="flex flex-col h-full bg-[#1E1E1E]">
            <EditorTabs />
            <div className="flex-1 overflow-hidden">
                <MonacoEditor />
            </div>
            <EditorStatusBar />
        </div>
    );
};