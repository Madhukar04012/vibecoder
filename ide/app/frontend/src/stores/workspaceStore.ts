import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { FileNode } from '../types';

interface WorkspaceState {
    files: FileNode[];
    currentProject: string;
    setFiles: (files: FileNode[]) => void;
    addFile: (parentPath: string, file: FileNode) => void;
    updateFile: (path: string, content: string) => void;
    deleteFile: (path: string) => void;
    renameFile: (oldPath: string, newPath: string) => void;
    toggleFolder: (path: string) => void;
    setCurrentProject: (name: string) => void;
}

const mockFileSystem: FileNode[] = [
    {
        id: '1',
        name: 'src',
        type: 'folder',
        path: '/src',
        isOpen: true,
        children: [
            {
                id: '2',
                name: 'components',
                type: 'folder',
                path: '/src/components',
                isOpen: true,
                children: [
                    {
                        id: '3',
                        name: 'App.tsx',
                        type: 'file',
                        path: '/src/components/App.tsx',
                        language: 'typescript',
                        content: `import React from 'react';
import { TopNavigationBar } from './layout/TopNavigationBar';
import { ActivityBar } from './layout/ActivityBar';
import { Sidebar } from './layout/Sidebar';
import { EditorArea } from './layout/EditorArea';

const App: React.FC = () => {
  return (
    <div className="h-screen w-screen flex flex-col">
      <TopNavigationBar />
      <div className="flex-1 flex overflow-hidden">
        <ActivityBar />
        <Sidebar />
        <EditorArea />
      </div>
    </div>
  );
};

export default App;`
                    },
                    {
                        id: '8',
                        name: 'Button.tsx',
                        type: 'file',
                        path: '/src/components/Button.tsx',
                        language: 'typescript',
                        content: `import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary';
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  onClick, 
  variant = 'primary' 
}) => {
  return (
    <button 
      onClick={onClick}
      className={\`btn btn-\${variant}\`}
    >
      {children}
    </button>
  );
};`
                    }
                ]
            },
            {
                id: '4',
                name: 'utils',
                type: 'folder',
                path: '/src/utils',
                isOpen: false,
                children: [
                    {
                        id: '5',
                        name: 'helpers.ts',
                        type: 'file',
                        path: '/src/utils/helpers.ts',
                        language: 'typescript',
                        content: `export const formatDate = (date: Date): string => {
  return date.toISOString().split('T')[0];
};

export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1);
};

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};`
                    }
                ]
            },
            {
                id: '9',
                name: 'styles',
                type: 'folder',
                path: '/src/styles',
                isOpen: false,
                children: [
                    {
                        id: '10',
                        name: 'globals.css',
                        type: 'file',
                        path: '/src/styles/globals.css',
                        language: 'css',
                        content: `@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --primary-color: #007ACC;
  --background-dark: #1E1E1E;
  --panel-dark: #252526;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', sans-serif;
  background-color: var(--background-dark);
  color: #CCCCCC;
}`
                    }
                ]
            }
        ]
    },
    {
        id: '6',
        name: 'package.json',
        type: 'file',
        path: '/package.json',
        language: 'json',
        content: `{
  "name": "cloud-ide",
  "version": "1.0.0",
  "description": "SSS-Class production-grade cloud IDE",
  "main": "index.js",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.5.0",
    "@monaco-editor/react": "^4.7.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}`
    },
    {
        id: '7',
        name: 'README.md',
        type: 'file',
        path: '/README.md',
        language: 'markdown',
        content: `# Cloud IDE

A modern, production-grade cloud IDE with AI-native workflow.

## Features

- **Monaco Editor**: Full-featured code editor with syntax highlighting
- **AI Assistant**: Context-aware code editing and suggestions
- **Git Integration**: Built-in source control management
- **Terminal**: Multi-tab terminal with command execution
- **File Explorer**: Tree-based file navigation
- **Command Palette**: Quick access to all commands (Ctrl+P)

## Tech Stack

- React + TypeScript
- Monaco Editor
- Zustand for state management
- Tailwind CSS for styling
- Framer Motion for animations

## Getting Started

\`\`\`bash
npm install
npm run dev
\`\`\`

## Keyboard Shortcuts

- \`Ctrl+P\`: Open Command Palette
- \`Ctrl+B\`: Toggle Sidebar
- \`Ctrl+\\\`\`: Toggle Terminal
- \`Ctrl+S\`: Save File

## Architecture

The application follows a modular architecture with:
- Zustand stores for state management
- Reusable components
- Custom hooks for common functionality
- Type-safe TypeScript throughout`
    }
];

export const useWorkspaceStore = create<WorkspaceState>()(
    persist(
        (set) => ({
            files: mockFileSystem,
            currentProject: 'cloud-ide',
            setFiles: (files) => set({ files }),
            addFile: (parentPath, file) =>
                set((state) => {
                    const addToFolder = (nodes: FileNode[]): FileNode[] => {
                        return nodes.map((node) => {
                            if (node.path === parentPath && node.type === 'folder') {
                                return {
                                    ...node,
                                    children: [...(node.children || []), file],
                                };
                            }
                            if (node.children) {
                                return { ...node, children: addToFolder(node.children) };
                            }
                            return node;
                        });
                    };
                    return { files: addToFolder(state.files) };
                }),
            updateFile: (path, content) =>
                set((state) => {
                    const updateInTree = (nodes: FileNode[]): FileNode[] => {
                        return nodes.map((node) => {
                            if (node.path === path) {
                                return { ...node, content, modified: true };
                            }
                            if (node.children) {
                                return { ...node, children: updateInTree(node.children) };
                            }
                            return node;
                        });
                    };
                    return { files: updateInTree(state.files) };
                }),
            deleteFile: (path) =>
                set((state) => {
                    const deleteFromTree = (nodes: FileNode[]): FileNode[] => {
                        return nodes.filter((node) => {
                            if (node.path === path) return false;
                            if (node.children) {
                                node.children = deleteFromTree(node.children);
                            }
                            return true;
                        });
                    };
                    return { files: deleteFromTree(state.files) };
                }),
            renameFile: (oldPath, newPath) =>
                set((state) => {
                    const renameInTree = (nodes: FileNode[]): FileNode[] => {
                        return nodes.map((node) => {
                            if (node.path === oldPath) {
                                return { ...node, path: newPath, name: newPath.split('/').pop() || '' };
                            }
                            if (node.children) {
                                return { ...node, children: renameInTree(node.children) };
                            }
                            return node;
                        });
                    };
                    return { files: renameInTree(state.files) };
                }),
            toggleFolder: (path) =>
                set((state) => {
                    const toggleInTree = (nodes: FileNode[]): FileNode[] => {
                        return nodes.map((node) => {
                            if (node.path === path && node.type === 'folder') {
                                return { ...node, isOpen: !node.isOpen };
                            }
                            if (node.children) {
                                return { ...node, children: toggleInTree(node.children) };
                            }
                            return node;
                        });
                    };
                    return { files: toggleInTree(state.files) };
                }),
            setCurrentProject: (name) => set({ currentProject: name }),
        }),
        {
            name: 'workspace-storage',
        }
    )
);