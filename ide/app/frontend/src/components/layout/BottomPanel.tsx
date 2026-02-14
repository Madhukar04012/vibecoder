import React from 'react';
import { Terminal as TerminalIcon, AlertCircle, FileText, Bug, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useUIStore } from '@/stores/uiStore';
import { Terminal } from '../terminal/Terminal';
import { TerminalTabs } from '../terminal/TerminalTabs';

type BottomView = 'terminal' | 'problems' | 'output' | 'debug';

export const BottomPanel: React.FC = () => {
    const bottomPanelVisible = useUIStore((state) => state.bottomPanelVisible);
    const toggleBottomPanel = useUIStore((state) => state.toggleBottomPanel);
    const [activeView, setActiveView] = React.useState<BottomView>('terminal');

    if (!bottomPanelVisible) return null;

    const tabs = [
        { id: 'terminal' as BottomView, icon: TerminalIcon, label: 'Terminal' },
        { id: 'problems' as BottomView, icon: AlertCircle, label: 'Problems' },
        { id: 'output' as BottomView, icon: FileText, label: 'Output' },
        { id: 'debug' as BottomView, icon: Bug, label: 'Debug Console' },
    ];

    const renderContent = () => {
        switch (activeView) {
            case 'terminal':
                return (
                    <div className="flex flex-col h-full">
                        <TerminalTabs />
                        <div className="flex-1 overflow-hidden">
                            <Terminal />
                        </div>
                    </div>
                );
            case 'problems':
                return (
                    <div className="flex items-center justify-center h-full text-[#858585]">
                        <div className="text-center">
                            <AlertCircle className="w-12 h-12 mx-auto mb-2" />
                            <p className="text-sm">No problems detected</p>
                        </div>
                    </div>
                );
            case 'output':
                return (
                    <div className="flex items-center justify-center h-full text-[#858585]">
                        <div className="text-center">
                            <FileText className="w-12 h-12 mx-auto mb-2" />
                            <p className="text-sm">Output logs</p>
                        </div>
                    </div>
                );
            case 'debug':
                return (
                    <div className="flex items-center justify-center h-full text-[#858585]">
                        <div className="text-center">
                            <Bug className="w-12 h-12 mx-auto mb-2" />
                            <p className="text-sm">Debug console</p>
                        </div>
                    </div>
                );
        }
    };

    return (
        <div className="h-full bg-[#252526] border-t border-[#3E3E42] flex flex-col">
            <div className="flex items-center justify-between bg-[#252526] border-b border-[#3E3E42]">
                <div className="flex items-center">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveView(tab.id)}
                            className={cn(
                                'flex items-center gap-2 px-4 py-2 text-sm border-b-2 transition-colors',
                                activeView === tab.id
                                    ? 'text-[#FFFFFF] border-[#007ACC]'
                                    : 'text-[#858585] border-transparent hover:text-[#CCCCCC]'
                            )}
                        >
                            <tab.icon className="w-4 h-4" />
                            {tab.label}
                        </button>
                    ))}
                </div>
                <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 mr-2 text-[#858585] hover:text-[#CCCCCC]"
                    onClick={toggleBottomPanel}
                >
                    <X className="w-4 h-4" />
                </Button>
            </div>
            <div className="flex-1 overflow-hidden">
                {renderContent()}
            </div>
        </div>
    );
};