import React from 'react';
import {
    Files,
    Search,
    GitBranch,
    Package,
    Sparkles,
    Terminal as TerminalIcon,
    Settings,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/stores/uiStore';
import { ActivityView } from '@/types';

interface ActivityItem {
    id: ActivityView;
    icon: React.ReactNode;
    label: string;
}

const activities: ActivityItem[] = [
    { id: 'explorer', icon: <Files className="w-6 h-6" />, label: 'Explorer' },
    { id: 'search', icon: <Search className="w-6 h-6" />, label: 'Search' },
    { id: 'git', icon: <GitBranch className="w-6 h-6" />, label: 'Source Control' },
    { id: 'extensions', icon: <Package className="w-6 h-6" />, label: 'Extensions' },
    { id: 'ai', icon: <Sparkles className="w-6 h-6" />, label: 'AI Agents' },
    { id: 'terminal', icon: <TerminalIcon className="w-6 h-6" />, label: 'Terminal' },
];

export const ActivityBar: React.FC = () => {
    const activeView = useUIStore((state) => state.activeView);
    const setActiveView = useUIStore((state) => state.setActiveView);

    return (
        <div className="w-12 bg-[#333333] border-r border-[#3E3E42] flex flex-col items-center py-2 flex-shrink-0">
            <div className="flex-1 flex flex-col gap-2">
                {activities.map((activity) => (
                    <button
                        key={activity.id}
                        onClick={() => setActiveView(activity.id)}
                        className={cn(
                            'w-12 h-12 flex items-center justify-center transition-all relative group hover:bg-[#2A2D2E]',
                            activeView === activity.id
                                ? 'text-white bg-[#2A2D2E]'
                                : 'text-[#CCCCCC]'
                        )}
                        title={activity.label}
                    >
                        {activity.icon}
                        {activeView === activity.id && (
                            <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-white rounded-r" />
                        )}
                        <div className="absolute left-full ml-2 px-3 py-1.5 bg-[#252526] border border-[#3E3E42] rounded text-xs text-[#CCCCCC] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50 shadow-lg">
                            {activity.label}
                        </div>
                    </button>
                ))}
            </div>

            <button
                onClick={() => setActiveView('settings')}
                className={cn(
                    'w-12 h-12 flex items-center justify-center transition-all hover:bg-[#2A2D2E]',
                    activeView === 'settings'
                        ? 'text-white bg-[#2A2D2E]'
                        : 'text-[#CCCCCC]'
                )}
                title="Settings"
            >
                <Settings className="w-6 h-6" />
            </button>
        </div>
    );
};