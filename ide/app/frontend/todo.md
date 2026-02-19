# SSS-Class Cloud IDE UI - Development Plan

## Design Guidelines

### Design References
- **VS Code Web**: Professional developer aesthetic, clean panels
- **Replit**: Modern cloud IDE, smooth interactions
- **Cursor**: AI-native workflow integration
- **Style**: Dark Mode Professional IDE + Minimal + Developer-Focused

### Color Palette
- Primary Background: #1E1E1E (VS Code Dark)
- Secondary Background: #252526 (Panel Background)
- Tertiary Background: #2D2D30 (Sidebar)
- Border: #3E3E42 (Subtle borders)
- Accent: #007ACC (VS Code Blue - active states)
- Success: #89D185 (Green - success states)
- Warning: #DDB100 (Yellow - warnings)
- Error: #F48771 (Red - errors)
- Text Primary: #CCCCCC (Light Gray)
- Text Secondary: #858585 (Muted Gray)

### Typography
- Font Family: 'Inter' for UI, 'JetBrains Mono' for code
- Heading1: Inter font-weight 600 (20px)
- Heading2: Inter font-weight 600 (16px)
- Body: Inter font-weight 400 (13px)
- Code: JetBrains Mono font-weight 400 (13px)
- Small: Inter font-weight 400 (11px)

### Key Component Styles
- **Panels**: Dark background (#252526), 1px border (#3E3E42)
- **Buttons**: Primary (#007ACC), Ghost (transparent hover #2A2D2E)
- **Tabs**: Inactive (#2D2D30), Active (#1E1E1E), bottom border accent
- **Icons**: 20px standard, #858585 inactive, #CCCCCC active
- **Inputs**: Dark (#3C3C3C), border (#3E3E42), focus border (#007ACC)

### Layout & Spacing
- Activity Bar: 48px width
- Sidebar: 300px default width (resizable 200-500px)
- Top Bar: 35px height
- Bottom Panel: 200px default height (resizable 100-400px)
- Panel gaps: 0px (seamless)
- Content padding: 8px-16px

### Images to Generate
1. **ide-hero-code-dark.jpg** - Dark themed code editor with syntax highlighting, professional developer workspace (Style: photorealistic, dark mood, high contrast)
2. **ai-assistant-icon.png** - Modern AI assistant icon, glowing effect, tech aesthetic (Style: 3d, tech, transparent background)
3. **git-integration-visual.jpg** - Git workflow visualization, branches and commits, dark theme (Style: minimalist, diagram, dark background)
4. **terminal-preview.jpg** - Terminal interface with command output, developer tools (Style: photorealistic, dark theme, code aesthetic)

---

## Development Tasks

### Phase 1: Foundation & Setup
1. Initialize shadcn-ui template with TypeScript
2. Install dependencies (zustand, monaco-editor, framer-motion, @monaco-editor/react)
3. Generate all 4 design images
4. Setup folder structure and core architecture

### Phase 2: State Management
5. Create Zustand stores (workspace, editor, ui, git, ai)
6. Implement file system state management
7. Setup theme system (dark/light)

### Phase 3: Core Layout Components
8. TopNavigationBar component
9. ActivityBar component (left vertical)
10. Sidebar component (context-based)
11. EditorArea component (multi-tab, split view)
12. AICopilotPanel component (right side)
13. BottomPanel component (terminal, problems, output)

### Phase 4: Advanced Features
14. Monaco Editor integration with full features
15. File Explorer with drag & drop
16. Command Palette (Ctrl+P)
17. Resizable panels system
18. Tab management and restore
19. Git integration UI
20. Terminal component (multi-tab)
21. AI chat interface with diff preview
22. Toast notification system
23. Keyboard shortcuts system

### Phase 5: Polish & Production
24. Error boundaries
25. Theme switcher
26. Workspace persistence (localStorage)
27. Responsive layout adjustments
28. Performance optimizations
29. Final testing and lint check

## File Structure
```
src/
├── components/
│   ├── layout/
│   │   ├── TopNavigationBar.tsx
│   │   ├── ActivityBar.tsx
│   │   ├── Sidebar.tsx
│   │   ├── EditorArea.tsx
│   │   ├── AICopilotPanel.tsx
│   │   └── BottomPanel.tsx
│   ├── editor/
│   │   ├── MonacoEditor.tsx
│   │   ├── EditorTabs.tsx
│   │   └── EditorStatusBar.tsx
│   ├── file-explorer/
│   │   ├── FileTree.tsx
│   │   ├── FileTreeItem.tsx
│   │   └── FileContextMenu.tsx
│   ├── terminal/
│   │   ├── Terminal.tsx
│   │   └── TerminalTabs.tsx
│   ├── ai/
│   │   ├── AIChatInterface.tsx
│   │   ├── DiffPreview.tsx
│   │   └── ToolVisualization.tsx
│   ├── git/
│   │   ├── GitPanel.tsx
│   │   └── GitChanges.tsx
│   ├── command-palette/
│   │   └── CommandPalette.tsx
│   ├── ui/
│   │   ├── ResizablePanel.tsx
│   │   ├── Toast.tsx
│   │   └── ErrorBoundary.tsx
│   └── shared/
│       ├── Icon.tsx
│       └── Button.tsx
├── stores/
│   ├── workspaceStore.ts
│   ├── editorStore.ts
│   ├── uiStore.ts
│   ├── gitStore.ts
│   └── aiStore.ts
├── hooks/
│   ├── useKeyboardShortcuts.ts
│   ├── useResizable.ts
│   └── useWorkspacePersistence.ts
├── types/
│   └── index.ts
├── utils/
│   ├── fileSystem.ts
│   └── shortcuts.ts
├── App.tsx
└── main.tsx
```