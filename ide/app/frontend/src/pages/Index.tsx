import { useEffect } from 'react';
import { useEditorStore } from '../stores/editorStore';
import { useWorkspaceStore } from '../stores/workspaceStore';

export default function Index() {
    const openTab = useEditorStore((state) => state.openTab);
    const files = useWorkspaceStore((state) => state.files);

    useEffect(() => {
        // Auto-open the App.tsx file on mount
        const findAppFile = (nodes: any[]): any => {
            for (const node of nodes) {
                if (node.path === '/src/components/App.tsx') {
                    return node;
                }
                if (node.children) {
                    const found = findAppFile(node.children);
                    if (found) return found;
                }
            }
            return null;
        };

        const appFile = findAppFile(files);
        if (appFile) {
            openTab(
                appFile.id,
                appFile.name,
                appFile.path,
                appFile.content || '',
                appFile.language || 'typescript'
            );
        }
    }, []);

    return null;
}