# VibeCober — Component Inventory Map

## 1️⃣ Global Shell

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **AtomsShell** | `NovaIDE.tsx` | ✅ Single component, owns layout grid |
| **TopBar** | `AtomsTopBar.tsx` | ✅ Extracted |
| **Sidebar** | `FilePanel` + inline AI input | ✅ In NovaIDE |
| **Workspace** | Inline in NovaIDE | ✅ |
| **atoms-ide-layout.css** | CSS vars | ✅ |

## 2️⃣ Top Bar

| Spec | Implementation | Status |
|------|----------------|--------|
| **TopBar** | `AtomsTopBar` | ✅ |
| **AppTitle** | "NOVA AI Assistant" (icon + project badge) | ✅ |
| **ViewModeSwitch** | Code \| Preview pills | ✅ |
| **UserActions** | Account hover panel | ✅ |

## 3️⃣ Sidebar

| Spec | Implementation | Status |
|------|----------------|--------|
| **Sidebar** | `FilePanel` + chat input | ✅ |
| **FileTree** | `FilePanel` (dynamic tree) | ✅ |
| **AIInputBar** | Inside `AtomsChatPanel` | ✅ |

## 4️⃣ Workspace

| Spec | Implementation | Status |
|------|----------------|--------|
| **Workspace** | `viewMode`: editor \| viewer | ✅ |
| **Editor** | `EditorPanel` + Monaco | ✅ |
| **AppPreview** | iframe, `previewUrl` | ✅ |

## 5️⃣ Editor

| Spec | Implementation | Status |
|------|----------------|--------|
| **EditorTabs** | `EditorTabs` | ✅ |
| **EditorPane** | `EditorCanvas` (Monaco) | ✅ |

## 6️⃣ Persistence

| Item | Implementation |
|------|----------------|
| Open tabs, active file | `ide-store.ts` (localStorage) |

## 7️⃣ Keyboard Shortcuts (reference)

| Shortcut | Action |
|----------|--------|
| Cmd/Ctrl+Enter | Switch Editor/Preview (via ATMOS phase) |

---

## Removed (Cleanup)

- IDE overlays: AtomManager, MarketplaceBrowser, AgentHierarchy, ClarificationPortal, CollaborationOverlay, MermaidPanel, OptimizationCenter, TestConsole, Terminal (Xterm)
- AtomsAgentTimelineOverlay, DiffReviewPanel, AtomsTerminalPanel, AtomsMikeMessage
- lib: studio.ts, ide-persistence.ts, ai-diff.ts, virtual-fs.ts
- Previous: SidebarDemo, AtomsSidebar, AtomsFileExplorer, AtomsQuickOpen, FileTree, agent-engine, useIDEUser, data/fileTree, App.tsx
