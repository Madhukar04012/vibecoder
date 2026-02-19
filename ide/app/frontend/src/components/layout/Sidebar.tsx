import React from 'react';
import { useUIStore } from '@/stores/uiStore';
import { FileTree } from '../file-explorer/FileTree';
import { GitPanel } from '../git/GitPanel';
import { Search, Package, Sparkles, Terminal as TerminalIcon, Settings } from 'lucide-react';

export const Sidebar: React.FC = () => {
    const activeView = useUIStore((state) => state.activeView);
    const sidebarVisible = useUIStore((state) => state.sidebarVisible);

    if (!sidebarVisible) return null;

    const renderContent = () => {
        switch (activeView) {
            case 'explorer':
                return <FileTree />;
            case 'git':
                return <GitPanel />;
            case 'search':
                return (
                    <div className="flex flex-col items-center justify-center h-full text-[#858585]">
                        <Search className="w-12 h-12 mb-4" />
                        <p className="text-sm">Search functionality</p>
                    </div>
                );
            case 'extensions':
                return (
                    <div className="flex flex-col items-center justify-center h-full text-[#858585]">
                        <Package className="w-12 h-12 mb-4" />
                        <p className="text-sm">Extensions marketplace</p>
                    </div>
                );
            case 'ai':
                return (
                    <div className="flex flex-col items-center justify-center h-full text-[#858585]">
                        <Sparkles className="w-12 h-12 mb-4" />
                        <p className="text-sm">AI Agents panel</p>
                    </div>
                );
            case 'terminal':
                return (
                    <div className="flex flex-col items-center justify-center h-full text-[#858585]">
                        <TerminalIcon className="w-12 h-12 mb-4" />
                        <p className="text-sm">Terminal view</p>
                    </div>
                );
            case 'settings':
                return (
                    <div className="flex flex-col items-center justify-center h-full text-[#858585]">
                        <Settings className="w-12 h-12 mb-4" />
                        <p className="text-sm">Settings panel</p>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="h-full bg-[#252526] border-r border-[#3E3E42] overflow-hidden">
            {renderContent()}
        </div>
    );
};