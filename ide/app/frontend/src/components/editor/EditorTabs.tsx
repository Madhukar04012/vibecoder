import React from 'react';
import { X, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useEditorStore } from '@/stores/editorStore';

export const EditorTabs: React.FC = () => {
    const tabs = useEditorStore((state) => state.tabs);
    const activeTabId = useEditorStore((state) => state.activeTabId);
    const setActiveTab = useEditorStore((state) => state.setActiveTab);
    const closeTab = useEditorStore((state) => state.closeTab);

    if (tabs.length === 0) return null;

    return (
        <div className="flex items-center bg-[#2D2D30] border-b border-[#3E3E42] overflow-x-auto">
            {tabs.map((tab) => (
                <div
                    key={tab.id}
                    className={cn(
                        'flex items-center gap-2 px-3 py-2 border-r border-[#3E3E42] cursor-pointer group min-w-[120px] max-w-[200px]',
                        tab.id === activeTabId
                            ? 'bg-[#1E1E1E] text-[#FFFFFF]'
                            : 'bg-[#2D2D30] text-[#858585] hover:text-[#CCCCCC]'
                    )}
                    onClick={() => setActiveTab(tab.id)}
                >
                    <span className="flex-1 truncate text-sm">{tab.title}</span>
                    {tab.isDirty && (
                        <Circle className="w-2 h-2 fill-[#007ACC] text-[#007ACC]" />
                    )}
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            closeTab(tab.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 hover:bg-[#3E3E42] rounded p-0.5 transition-opacity"
                    >
                        <X className="w-3.5 h-3.5" />
                    </button>
                </div>
            ))}
        </div>
    );
};