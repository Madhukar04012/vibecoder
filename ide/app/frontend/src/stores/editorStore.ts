import { create } from 'zustand';
import { EditorTab } from '../types';

interface EditorState {
    tabs: EditorTab[];
    activeTabId: string | null;
    splitView: boolean;
    secondaryTabId: string | null;
    openTab: (fileId: string, title: string, path: string, content: string, language: string) => void;
    closeTab: (tabId: string) => void;
    setActiveTab: (tabId: string) => void;
    updateTabContent: (tabId: string, content: string) => void;
    markTabDirty: (tabId: string, isDirty: boolean) => void;
    toggleSplitView: () => void;
    setSecondaryTab: (tabId: string | null) => void;
    closeAllTabs: () => void;
    saveTab: (tabId: string) => void;
}

export const useEditorStore = create<EditorState>((set) => ({
    tabs: [],
    activeTabId: null,
    splitView: false,
    secondaryTabId: null,
    openTab: (fileId, title, path, content, language) =>
        set((state) => {
            const existingTab = state.tabs.find((tab) => tab.fileId === fileId);
            if (existingTab) {
                return { activeTabId: existingTab.id };
            }
            const newTab: EditorTab = {
                id: `tab-${Date.now()}`,
                fileId,
                title,
                path,
                content,
                language,
                isDirty: false,
                isActive: true,
            };
            return {
                tabs: [...state.tabs.map((tab) => ({ ...tab, isActive: false })), newTab],
                activeTabId: newTab.id,
            };
        }),
    closeTab: (tabId) =>
        set((state) => {
            const newTabs = state.tabs.filter((tab) => tab.id !== tabId);
            let newActiveTabId = state.activeTabId;
            if (state.activeTabId === tabId && newTabs.length > 0) {
                newActiveTabId = newTabs[newTabs.length - 1].id;
            } else if (newTabs.length === 0) {
                newActiveTabId = null;
            }
            return {
                tabs: newTabs,
                activeTabId: newActiveTabId,
                secondaryTabId: state.secondaryTabId === tabId ? null : state.secondaryTabId,
            };
        }),
    setActiveTab: (tabId) =>
        set((state) => ({
            tabs: state.tabs.map((tab) => ({ ...tab, isActive: tab.id === tabId })),
            activeTabId: tabId,
        })),
    updateTabContent: (tabId, content) =>
        set((state) => ({
            tabs: state.tabs.map((tab) =>
                tab.id === tabId ? { ...tab, content, isDirty: true } : tab
            ),
        })),
    markTabDirty: (tabId, isDirty) =>
        set((state) => ({
            tabs: state.tabs.map((tab) => (tab.id === tabId ? { ...tab, isDirty } : tab)),
        })),
    toggleSplitView: () => set((state) => ({ splitView: !state.splitView })),
    setSecondaryTab: (tabId) => set({ secondaryTabId: tabId }),
    closeAllTabs: () => set({ tabs: [], activeTabId: null, secondaryTabId: null }),
    saveTab: (tabId) =>
        set((state) => ({
            tabs: state.tabs.map((tab) => (tab.id === tabId ? { ...tab, isDirty: false } : tab)),
        })),
}));