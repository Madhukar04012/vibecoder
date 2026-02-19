import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ActivityView, Theme } from '../types';

interface UIState {
    theme: Theme;
    activeView: ActivityView;
    sidebarWidth: number;
    bottomPanelHeight: number;
    aiPanelWidth: number;
    sidebarVisible: boolean;
    bottomPanelVisible: boolean;
    aiPanelVisible: boolean;
    commandPaletteOpen: boolean;
    setTheme: (theme: Theme) => void;
    setActiveView: (view: ActivityView) => void;
    setSidebarWidth: (width: number) => void;
    setBottomPanelHeight: (height: number) => void;
    setAIPanelWidth: (width: number) => void;
    toggleSidebar: () => void;
    toggleBottomPanel: () => void;
    toggleAIPanel: () => void;
    toggleCommandPalette: () => void;
}

export const useUIStore = create<UIState>()(
    persist(
        (set) => ({
            theme: 'dark',
            activeView: 'explorer',
            sidebarWidth: 300,
            bottomPanelHeight: 200,
            aiPanelWidth: 400,
            sidebarVisible: true,
            bottomPanelVisible: true,
            aiPanelVisible: true,
            commandPaletteOpen: false,
            setTheme: (theme) => set({ theme }),
            setActiveView: (view) => set({ activeView: view }),
            setSidebarWidth: (width) => set({ sidebarWidth: Math.max(200, Math.min(500, width)) }),
            setBottomPanelHeight: (height) => set({ bottomPanelHeight: Math.max(100, Math.min(400, height)) }),
            setAIPanelWidth: (width) => set({ aiPanelWidth: Math.max(300, Math.min(600, width)) }),
            toggleSidebar: () => set((state) => ({ sidebarVisible: !state.sidebarVisible })),
            toggleBottomPanel: () => set((state) => ({ bottomPanelVisible: !state.bottomPanelVisible })),
            toggleAIPanel: () => set((state) => ({ aiPanelVisible: !state.aiPanelVisible })),
            toggleCommandPalette: () => set((state) => ({ commandPaletteOpen: !state.commandPaletteOpen })),
        }),
        {
            name: 'ui-storage',
        }
    )
);