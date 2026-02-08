# Current Code → Atoms Component Inventory Map

## 1️⃣ Global Shell

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **AtomsShell** | `NovaIDE.tsx` | ✅ Exists — single component, owns layout grid |
| **TopBar** | Inline in NovaIDE (lines 665–727) | ✅ Exists — not extracted |
| **Sidebar** | Inline in NovaIDE (lines 730–794) | ✅ Exists — not extracted |
| **Workspace** | Inline in NovaIDE (lines 796–899) | ✅ Exists — not extracted |
| **atoms-ide-layout.css** | CSS vars | ✅ Exists |

## 2️⃣ Top Bar Components

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **TopBar** | `<header>` in NovaIDE | ✅ |
| **AppTitle** | Inline: "NOVA AI Assistant" | ✅ |
| **ViewModeSwitch** | Inline pill buttons (Editor \| App) | ✅ |
| **UserActions** | Avatar + Share2 (Publish) | ✅ |
| **PublishButton** | Share2 icon, `handlePublish`, disabled during build | ✅ |

## 3️⃣ Sidebar

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **Sidebar** | `<aside>` with FileTree + AIInputBar | ✅ |
| **FileTree** | `FileTreeItem` + `displayFileTree` in NovaIDE | ✅ Inline |
| **AIInputBar** | Single-line input + ArrowUp button | ✅ Inline |
| Chat list / status / banners | — | ✅ None |

## 4️⃣ Workspace

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **Workspace** | `viewMode === 'editor'` vs `viewMode === 'viewer'` | ✅ |
| **Editor** | Tab bar + Monaco | ✅ |
| **AppPreview** | iframe, `previewUrl` | ✅ |
| `projectLoaded` | `workspaceMode`, `isEmptyWorkspace` | ✅ |

## 5️⃣ Editor Side

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **EditorWorkspace** | Inline in NovaIDE | ✅ |
| **EditorTabs** | Tab bar with `openTabs`, `activeTab`, close | ✅ |
| **EditorPane** | Monaco + `ATOMS_MONACO_OPTIONS` | ✅ |
| **EditorEmptyState** | "Select a file", opacity 0.35 | ✅ |
| **DiffReviewEditor** | Used when `pendingDiffs` | ✅ |

## 6️⃣ App Preview Side

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **AppPreview** | iframe `src={previewUrl \|\| 'about:blank'}` | ✅ |
| Start/stop preview | `startPreview` in effect | ✅ |
| No loaders/messages | Blank iframe | ✅ |

## 7️⃣ Overlays

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **QuickOpenOverlay** | `AtomsQuickOpen` mode `file` | ✅ |
| **CommandPalette** | `AtomsQuickOpen` mode `command` | ✅ |
| Commands | Switch to Editor, App, Toggle Sidebar, Split, Build | ✅ |

## 8️⃣ Split Editor

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **SplitEditor** | `splitEditor` state, two Monaco instances | ✅ |
| Toggle shortcut | Cmd/Ctrl+\\ | ✅ |

## 9️⃣ AI Execution UI (invisible / modal only)

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **IntentPreviewPanel** | `IntentPreviewPanel` — plan approve/reject | ✅ |
| **DiffReviewPanel** | `DiffReviewPanel` — diff approve/reject | ⚠️ See note |
| **AIIntentPanel** | Different flow: `pendingIntent` (AIIntent) | ⚠️ Two intent flows |
| **ActivityLog** | `addActivity` in store, not rendered | ✅ Correct |

**Note:** `DiffReviewPanel` exists but diff review is also handled inline via `DiffReviewEditor` when `pendingDiffs` has a match. Two mechanisms: (1) `DiffReviewPanel` for `pendingDiffPlan`, (2) inline `DiffReviewEditor` for `pendingDiffs`. Verify which path is primary.

## 🔟 Keyboard Controller

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **KeyboardManager** | `useEffect` keydown handler in NovaIDE | ✅ Inline |
| Cmd/Ctrl+P | Quick open | ✅ |
| Cmd/Ctrl+Shift+P | Command palette | ✅ |
| Cmd/Ctrl+B | Toggle sidebar | ✅ |
| Cmd/Ctrl+\\ | Toggle split | ✅ |
| Cmd/Ctrl+Enter | Switch Editor/App | ✅ |

## 1️⃣1️⃣ Persistence

| Spec | Current Implementation | Status |
|------|------------------------|--------|
| **IDEStatePersistence** | `ide-persistence.ts` | ✅ |
| `loadIDEState`, `saveIDEState` | Used in NovaIDE | ✅ |
| Open tabs, active file, cursor, scroll, sidebar, view mode | Persisted | ✅ |

---

## ❌ Components That Must NOT Exist (delete list)

| Component | File | Used? | Action |
|-----------|------|-------|--------|
| **AgentChatMessage** | `AgentChatMessage.tsx` | No | **DELETE** |
| **AgentPanel** | `AgentPanel.tsx` | No | **DELETE** |
| **AIActivityTimeline** | `AIActivityTimeline.tsx` | No | **DELETE** |
| **AIStartPanel** | `AIStartPanel.tsx` | No | **DELETE** |
| **AIModeToggle** | `AIModeToggle.tsx` | No | **DELETE** |
| **ProjectStateIndicator** | `ProjectStateIndicator.tsx` | No | **DELETE** |

None of these are imported anywhere. Safe to delete.

---

## ⚠️ Minor Leaks / Cleanup

| Item | Location | Action |
|------|----------|--------|
| **ModeSwitcher** | `ModeSwitcher.tsx` | KEEP — only `ViewMode` type is imported; component unused. Could move type to `ide-store` or a shared types file if desired. |
| **AIIntentPanel vs IntentPreviewPanel** | Both exist | Two intent flows: `AIIntentPanel` (pendingIntent) and `IntentPreviewPanel` (pendingPlan). Both are modals. If only one is needed, consolidate. |
| **DiffReviewPanel vs DiffReviewEditor** | Both used | `DiffReviewPanel` — full diff plan UI. `DiffReviewEditor` — inline per-file diff. Both serve different phases. OK. |

---

## Summary

- **Shell, TopBar, Sidebar, Workspace, Editor, AppPreview, Overlays, Split, Persistence:** All present and correct.
- **6 files to delete:** `AgentChatMessage.tsx`, `AgentPanel.tsx`, `AIActivityTimeline.tsx`, `AIStartPanel.tsx`, `AIModeToggle.tsx`, `ProjectStateIndicator.tsx`
- **No layout or copy changes** — only removal of dead components.
