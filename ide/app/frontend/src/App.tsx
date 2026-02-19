import React, { useEffect } from 'react';
import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { TopNavigationBar } from './components/layout/TopNavigationBar';
import { ActivityBar } from './components/layout/ActivityBar';
import { Sidebar } from './components/layout/Sidebar';
import { EditorArea } from './components/layout/EditorArea';
import { AICopilotPanel } from './components/layout/AICopilotPanel';
import { BottomPanel } from './components/layout/BottomPanel';
import { CommandPalette } from './components/command-palette/CommandPalette';
import { ResizablePanel } from './components/shared/ResizablePanel';
import { useUIStore } from './stores/uiStore';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';

const App: React.FC = () => {
    const theme = useUIStore((state) => state.theme);
    const sidebarWidth = useUIStore((state) => state.sidebarWidth);
    const bottomPanelHeight = useUIStore((state) => state.bottomPanelHeight);
    const aiPanelWidth = useUIStore((state) => state.aiPanelWidth);
    const sidebarVisible = useUIStore((state) => state.sidebarVisible);
    const bottomPanelVisible = useUIStore((state) => state.bottomPanelVisible);
    const aiPanelVisible = useUIStore((state) => state.aiPanelVisible);
    const setSidebarWidth = useUIStore((state) => state.setSidebarWidth);
    const setBottomPanelHeight = useUIStore((state) => state.setBottomPanelHeight);
    const setAIPanelWidth = useUIStore((state) => state.setAIPanelWidth);
    const toggleCommandPalette = useUIStore((state) => state.toggleCommandPalette);
    const toggleSidebar = useUIStore((state) => state.toggleSidebar);
    const toggleBottomPanel = useUIStore((state) => state.toggleBottomPanel);

    useKeyboardShortcuts([
        {
            key: 'p',
            ctrl: true,
            action: toggleCommandPalette,
            description: 'Open Command Palette',
        },
        {
            key: 'b',
            ctrl: true,
            action: toggleSidebar,
            description: 'Toggle Sidebar',
        },
        {
            key: '`',
            ctrl: true,
            action: toggleBottomPanel,
            description: 'Toggle Terminal',
        },
    ]);

    useEffect(() => {
        document.documentElement.classList.toggle('dark', theme === 'dark');
    }, [theme]);

    return (
        <TooltipProvider>
            <div className="h-screen w-screen flex flex-col bg-[#1E1E1E] text-[#CCCCCC] overflow-hidden">
                <TopNavigationBar />

                <div className="flex-1 flex overflow-hidden">
                    <ActivityBar />

                    {sidebarVisible && (
                        <ResizablePanel
                            direction="horizontal"
                            size={sidebarWidth}
                            onResize={setSidebarWidth}
                            minSize={200}
                            maxSize={500}
                        >
                            <Sidebar />
                        </ResizablePanel>
                    )}

                    <div className="flex-1 flex flex-col overflow-hidden">
                        <div className="flex-1 flex overflow-hidden">
                            <div className="flex-1 flex flex-col overflow-hidden">
                                {bottomPanelVisible ? (
                                    <>
                                        <div style={{ flex: `1 1 calc(100% - ${bottomPanelHeight}px)` }} className="overflow-hidden">
                                            <EditorArea />
                                        </div>
                                        <ResizablePanel
                                            direction="vertical"
                                            size={bottomPanelHeight}
                                            onResize={setBottomPanelHeight}
                                            minSize={100}
                                            maxSize={400}
                                        >
                                            <BottomPanel />
                                        </ResizablePanel>
                                    </>
                                ) : (
                                    <EditorArea />
                                )}
                            </div>

                            {aiPanelVisible && (
                                <ResizablePanel
                                    direction="horizontal"
                                    size={aiPanelWidth}
                                    onResize={setAIPanelWidth}
                                    minSize={300}
                                    maxSize={600}
                                >
                                    <AICopilotPanel />
                                </ResizablePanel>
                            )}
                        </div>
                    </div>
                </div>

                <CommandPalette />
                <Toaster />
            </div>
        </TooltipProvider>
    );
};

export default App;