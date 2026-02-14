import React from 'react';
import { useEditorStore } from '@/stores/editorStore';
import { AlertCircle, CheckCircle } from 'lucide-react';

export const EditorStatusBar: React.FC = () => {
    const tabs = useEditorStore((state) => state.tabs);
    const activeTabId = useEditorStore((state) => state.activeTabId);
    const activeTab = tabs.find((tab) => tab.id === activeTabId);

    return (
        <div className="h-[22px] bg-[#007ACC] flex items-center justify-between px-3 text-white text-xs">
            <div className="flex items-center gap-4">
                {activeTab && (
                    <>
                        <span>{activeTab.language.toUpperCase()}</span>
                        <span>UTF-8</span>
                        <span>LF</span>
                    </>
                )}
            </div>
            <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>No Issues</span>
                </div>
                {activeTab?.isDirty && (
                    <div className="flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" />
                        <span>Unsaved</span>
                    </div>
                )}
            </div>
        </div>
    );
};