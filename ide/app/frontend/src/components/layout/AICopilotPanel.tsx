import React from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUIStore } from '@/stores/uiStore';
import { AIChatInterface } from '../ai/AIChatInterface';
import { DiffPreview } from '../ai/DiffPreview';

export const AICopilotPanel: React.FC = () => {
    const aiPanelVisible = useUIStore((state) => state.aiPanelVisible);
    const toggleAIPanel = useUIStore((state) => state.toggleAIPanel);

    if (!aiPanelVisible) return null;

    return (
        <div className="h-full bg-[#252526] border-l border-[#3E3E42] flex flex-col">
            <div className="flex items-center justify-between px-4 py-2 border-b border-[#3E3E42]">
                <span className="text-[#CCCCCC] text-sm font-medium">AI Assistant</span>
                <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 text-[#858585] hover:text-[#CCCCCC]"
                    onClick={toggleAIPanel}
                >
                    <X className="w-4 h-4" />
                </Button>
            </div>
            <div className="flex-1 overflow-hidden">
                <AIChatInterface />
            </div>
            <DiffPreview />
        </div>
    );
};