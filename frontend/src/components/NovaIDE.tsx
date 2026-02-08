import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Group, Panel, Separator } from 'react-resizable-panels';
import { ChevronRight, ChevronDown, X, ArrowUp, ExternalLink } from 'lucide-react';
import { Editor } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';
import { cn } from '@/lib/utils';
import { AIIntentPanel } from '@/components/AIIntentPanel';
import { IntentPreviewPanel } from '@/components/IntentPreviewPanel';
import { DiffReviewPanel } from '@/components/DiffReviewPanel';
import { AtomsQuickOpen, type QuickOpenMode } from '@/components/AtomsQuickOpen';
import type { ViewMode } from '@/components/ModeSwitcher';
import { AtomsTopBar } from '@/components/AtomsTopBar';
import { AtomsChatPanel } from '@/components/AtomsChatPanel';
import { AtomsFileExplorer, type FileExplorerNode } from '@/components/AtomsFileExplorer';
import { AtomsTerminalPanel } from '@/components/AtomsTerminalPanel';
import { useIDEStore } from '@/stores/ide-store';
import { DiffReviewEditor } from '@/components/DiffReviewEditor';
import { applyChange } from '@/lib/studio';
import { applyDiffActionToContent, type DiffPlan } from '@/lib/diff';
import { shouldAutoApprove } from '@/lib/autonomy';
import { ATOMS_DARK_THEME, ATOMS_MONACO_OPTIONS } from '@/lib/monaco-atoms-theme';
import { loadIDEState, saveIDEState, type CursorState } from '@/lib/ide-persistence';
import type * as Monaco from 'monaco-editor';

const getIDEState = () => useIDEStore.getState();

const PERSIST_DEBOUNCE_MS = 300;

import {
  getProjectTree,
  getPlan,
  getDiffPlan,
  getFileContent,
  runEngineer,
  executeCommand,
  startPreview,
  type FileNode as StudioFileNode,
  type Plan as StudioPlan,
} from '@/lib/studio';

interface FileNode {
  name: string;
  type: 'file' | 'folder';
  fullName?: string;
  path?: string;
  children?: FileNode[];
}

function getFileExt(name: string) {
  const m = name.match(/\.(\w+)$/);
  return m ? m[1].toUpperCase().slice(0, 2) : 'TX';
}

function FileTreeItem({
  node,
  level,
  selected,
  onSelect,
}: {
  node: FileNode;
  level: number;
  selected: string | null;
  onSelect: (path: string, name: string) => void;
}) {
  const [open, setOpen] = useState(level < 4);
  const isFolder = node.type === 'folder';
  const isSelected = selected === (node.path || node.fullName || node.name);
  const hasChildren = isFolder && node.children && node.children.length > 0;

  if (isFolder) {
    return (
      <div className="select-none">
        <div
          className="flex items-center gap-1 px-2 py-0.5 text-[13px] text-[#e3e3e3] hover:bg-[#333] cursor-pointer"
          style={{ paddingLeft: `${level * 12 + 8}px` }}
          onClick={() => setOpen(!open)}
        >
          {hasChildren ? (
            open ? (
              <ChevronDown className="w-3.5 h-3.5 text-[#8b8b8b] shrink-0" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-[#8b8b8b] shrink-0" />
            )
          ) : (
            <span className="w-3.5" />
          )}
          <span className="truncate">{node.name}</span>
        </div>
        {hasChildren && open && (
          <div>
            {node.children!.map((child, i) => (
              <FileTreeItem
                key={i}
                node={child}
                level={level + 1}
                selected={selected}
                onSelect={onSelect}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex items-center gap-1.5 px-2 py-0.5 text-[13px] cursor-pointer',
        isSelected ? 'bg-[#3a3a3a] text-white' : 'text-[#e3e3e3] hover:bg-[#333]'
      )}
      style={{ paddingLeft: `${level * 12 + 24}px` }}
      onClick={() => onSelect(node.path || node.fullName || node.name || '', node.fullName || node.name)}
    >
      <span className="text-[11px] shrink-0">{getFileExt(node.name)}</span>
      <span className="truncate">{node.name}</span>
    </div>
  );
}

function studioFileNodeToLocal(node: StudioFileNode): FileNode {
  return {
    name: node.name,
    type: node.type,
    path: node.path,
    fullName: node.type === 'file' ? node.name : undefined,
    children: node.children?.map(studioFileNodeToLocal),
  };
}

function collectFilesFromTree(nodes: FileNode[], basePath = ''): { path: string; name: string }[] {
  const out: { path: string; name: string }[] = [];
  for (const node of nodes) {
    const path = node.path || node.fullName || node.name;
    if (node.type === 'file') {
      out.push({ path, name: node.fullName || node.name });
    }
    if (node.children?.length) {
      out.push(...collectFilesFromTree(node.children, path));
    }
  }
  return out;
}

function fileNodeToExplorerNode(node: FileNode): FileExplorerNode {
  return {
    name: node.name,
    type: node.type,
    path: node.path || node.fullName || node.name,
    children: node.children?.map(fileNodeToExplorerNode),
  };
}

export default function NovaIDE() {
  const PROJECT_ID = 'demo';
  const {
    workspaceMode,
    setWorkspaceMode,
    project,
    setProject,
    setProjectState,
    addActivity,
    showPlan,
    clearPlanPanel,
    dismissPlan,
    showDiffReview,
    dismissDiffReview,
    projectState,
    pendingDiffs,
    resolveDiff,
  } = useIDEStore();
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [openTabs, setOpenTabs] = useState<{ path: string; name: string }[]>([]);
  const [activeTab, setActiveTab] = useState<string>('');
  const [fileContents, setFileContents] = useState<Record<string, string>>({});
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('editor');
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [splitEditor, setSplitEditor] = useState(false);
  const [quickOpenMode, setQuickOpenMode] = useState<QuickOpenMode | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [publishLoading, setPublishLoading] = useState(false);
  const chatInputRef = useRef<HTMLInputElement>(null);
  const editorRef = useRef<Monaco.editor.IStandaloneCodeEditor | null>(null);
  const cursorStatesRef = useRef<Record<string, CursorState>>({});
  const persistTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hasRestoredRef = useRef(false);

  // Persist on beforeunload (sync save of cursor)
  useEffect(() => {
    const handler = () => {
      const editor = editorRef.current;
      if (editor && activeTab) {
        try {
          const pos = editor.getPosition();
          const scrollTop = editor.getScrollTop();
          if (pos) {
            cursorStatesRef.current = {
              ...cursorStatesRef.current,
              [activeTab]: { line: pos.lineNumber, column: pos.column, scrollTop },
            };
          }
        } catch {
          // ignore
        }
      }
      saveIDEState({
        projectId: PROJECT_ID,
        activeTab,
        openTabs,
        viewMode,
        sidebarVisible,
        cursorStates: cursorStatesRef.current,
      });
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [activeTab, openTabs, viewMode, sidebarVisible]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey;
      if (mod && e.shiftKey && e.key === 'P') {
        e.preventDefault();
        setQuickOpenMode('command');
        return;
      }
      if (mod && e.key === 'p') {
        e.preventDefault();
        setQuickOpenMode('file');
        return;
      }
      if (mod && e.key === 'b') {
        e.preventDefault();
        setSidebarVisible((v) => !v);
        return;
      }
      if (mod && e.key === '\\') {
        e.preventDefault();
        setSplitEditor((v) => !v);
        return;
      }
      if (mod && e.key === '`') {
        e.preventDefault();
        setViewMode((m) => (m === 'terminal' ? 'editor' : 'terminal'));
        return;
      }
      if (mod && e.key === 'Enter') {
        e.preventDefault();
        setViewMode((m) => (m === 'editor' ? 'viewer' : 'editor'));
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const normalizePlan = useCallback((raw: unknown): StudioPlan => {
    if (!raw || typeof raw !== 'object') {
      return { summary: 'Plan unavailable', actions: { createFiles: [], modifyFiles: [], runCommands: [] } };
    }
    const o = raw as Record<string, unknown>;
    const plan = o.plan as Record<string, unknown> | undefined;
    const actions = (plan?.actions ?? o.actions) as Record<string, unknown> | undefined;
    const summary = String(plan?.summary ?? o.summary ?? 'AI-generated plan').slice(0, 500);
    const create = Array.isArray(actions?.createFiles) ? actions.createFiles.map(String).slice(0, 50) : [];
    const modify = Array.isArray(actions?.modifyFiles) ? actions.modifyFiles.map(String).slice(0, 50) : [];
    const run = Array.isArray(actions?.runCommands) ? actions.runCommands.map(String).slice(0, 20) : [];
    return { summary, actions: { createFiles: create, modifyFiles: modify, runCommands: run } };
  }, []);

  const runPlanner = useCallback(
    async (prompt: string): Promise<StudioPlan> => {
      try {
        const res = await getPlan(prompt);
        return normalizePlan(res);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Planner failed';
        return {
          summary: `Plan for: ${prompt.slice(0, 80)}${prompt.length > 80 ? '…' : ''}`,
          actions: { createFiles: [], modifyFiles: [], runCommands: ['npm install'] },
        };
      }
    },
    [normalizePlan]
  );

  const executeUserIntent = useCallback(
    async (prompt: string) => {
      setChatInput('');
      setChatLoading(true);
      setProjectState('ai_running');
      addActivity('AI processing', prompt.slice(0, 50));
      const plan = await runPlanner(prompt);
      showPlan(plan);
      setChatLoading(false);
    },
    [setProjectState, addActivity, runPlanner, showPlan]
  );

  const handleSend = useCallback(() => {
    const trimmed = chatInput.trim();
    if (!trimmed) return;
    executeUserIntent(trimmed);
  }, [chatInput, executeUserIntent]);

  const refreshFileTree = useCallback(() => {
    getProjectTree(PROJECT_ID)
      .then((nodes) => {
        setFileTree(nodes.map(studioFileNodeToLocal));
        if (nodes.length > 0) {
          const rootName = nodes[0]?.name || PROJECT_ID;
          setProject({ id: PROJECT_ID, name: rootName });
        }
      })
      .catch(() => {
        setFileTree([]);
        setProject(null);
      });
  }, [setProject]);

  const applyApprovedDiffPlan = useCallback(
    async (diffPlan: DiffPlan) => {
      setProjectState('applying_diffs');
      setChatLoading(true);
      addActivity('Applying code changes', diffPlan.summary);

      const byFile = new Map<string, typeof diffPlan.diffs>();
      for (const d of diffPlan.diffs) {
        const f = d.file;
        if (!byFile.has(f)) byFile.set(f, []);
        byFile.get(f)!.push(d);
      }

      const checkpoint: Record<string, string> = {};
      for (const filePath of byFile.keys()) {
        try {
          const r = await getFileContent(PROJECT_ID, filePath);
          checkpoint[filePath] = r.content;
        } catch {
          throw new Error(`File not found: ${filePath}`);
        }
      }

      const handleFailure = async (err: unknown, modifiedFiles: string[]) => {
        const msg = err instanceof Error ? err.message : String(err);
        addActivity('Code changes failed', msg, false);
        if (modifiedFiles.length > 0) {
          addActivity('Rolling back modified files');
          for (const filePath of modifiedFiles) {
            try {
              await applyChange(PROJECT_ID, filePath, checkpoint[filePath]);
            } catch (e) {
              addActivity('Rollback failed', `${filePath}: ${(e as Error)?.message}`, false);
            }
          }
          addActivity('Rollback completed');
        }
        setProjectState(getIDEState().project ? 'loaded' : 'no_project');
        setChatLoading(false);
        dismissDiffReview();
      };

      const modifiedFiles: string[] = [];
      try {
        for (const [filePath, diffs] of byFile) {
          addActivity(`Applying diffs to ${filePath}`);
          let result = checkpoint[filePath];
          for (const d of diffs) {
            result = applyDiffActionToContent(result, d);
          }
          const res = await applyChange(PROJECT_ID, filePath, result);
          if (!res.success) throw new Error(res.error ?? `Failed to write ${filePath}`);
          modifiedFiles.push(filePath);
        }
        addActivity('Code changes applied', undefined, true);
        setWorkspaceMode('project');
        setProject({ id: PROJECT_ID, name: 'demo' });
        setProjectState('loaded');
        setChatLoading(false);
        dismissDiffReview();
        refreshFileTree();
      } catch (err) {
        await handleFailure(err, modifiedFiles);
      }
    },
    [setProjectState, setWorkspaceMode, setProject, setChatLoading, addActivity, dismissDiffReview, refreshFileTree]
  );

  const executeApprovedPlan = useCallback(
    async (plan: StudioPlan) => {
      clearPlanPanel();
      setProjectState('executing');
      setChatLoading(true);
      addActivity('Execution started', plan.summary);

      const finalizeExecution = () => {
        setWorkspaceMode('project');
        setProject({ id: PROJECT_ID, name: 'demo' });
        setProjectState('loaded');
        setChatLoading(false);
        addActivity('Execution completed', undefined, true);
        dismissPlan();
        refreshFileTree();
      };

      const handleExecutionFailure = (err: unknown) => {
        const msg = err instanceof Error ? err.message : String(err);
        addActivity('Execution failed', msg, false);
        setProjectState(getIDEState().project ? 'loaded' : 'no_project');
        setChatLoading(false);
        dismissPlan();
      };

      try {
        for (const file of plan.actions.createFiles) {
          const path = file.replace(/^\/+/, '').trim();
          if (!path) continue;
          addActivity(`Engineer generating: ${path}`);
          const { content } = await runEngineer(plan, path);
          addActivity(`Creating file: ${path}`);
          const res = await applyChange(PROJECT_ID, path, content);
          if (!res.success) throw new Error(res.error ?? `Failed to create ${file}`);
        }
        for (const cmd of plan.actions.runCommands) {
          if (!cmd.trim()) continue;
          addActivity(`Running: ${cmd}`);
          const res = await executeCommand(PROJECT_ID, cmd);
          if (!res.success) throw new Error(res.output || `Command failed: ${cmd}`);
        }
        if (plan.actions.modifyFiles.length > 0) {
          const files: Record<string, string> = {};
          for (const path of plan.actions.modifyFiles) {
            const p = path.replace(/^\/+/, '').trim();
            if (!p) continue;
            try {
              const r = await getFileContent(PROJECT_ID, p);
              files[p] = r.content;
            } catch {
              files[p] = '';
            }
          }
          const { diffPlan } = await getDiffPlan(plan, files);
          if (diffPlan.diffs.length > 0) {
            const decision = shouldAutoApprove(diffPlan);
            if (decision.autoApprove) {
              addActivity('Auto-approved (low risk)', decision.reason);
              await applyApprovedDiffPlan(diffPlan);
            } else {
              setChatLoading(false);
              showDiffReview(diffPlan, files);
            }
          } else {
            finalizeExecution();
          }
        } else {
          finalizeExecution();
        }
      } catch (err) {
        handleExecutionFailure(err);
      }
    },
    [clearPlanPanel, setProjectState, setChatLoading, addActivity, setWorkspaceMode, setProject, dismissPlan, showDiffReview, applyApprovedDiffPlan, refreshFileTree]
  );

  // On mount: if we have saved state, restore to project mode
  useEffect(() => {
    if (workspaceMode === 'empty' && loadIDEState(PROJECT_ID)) {
      setWorkspaceMode('project');
    }
  }, [workspaceMode, setWorkspaceMode]);

  useEffect(() => {
    if (workspaceMode !== 'project') return;
    refreshFileTree();
  }, [workspaceMode, refreshFileTree]);

  // Restore from persistence when project loads (once per session)
  useEffect(() => {
    if (workspaceMode !== 'project' || fileTree.length === 0 || hasRestoredRef.current) return;
    const saved = loadIDEState(PROJECT_ID);
    if (!saved) return;
    hasRestoredRef.current = true;
    const validPaths = new Set<string>();
    const collect = (nodes: FileNode[]) => {
      for (const n of nodes) {
        if (n.path) validPaths.add(n.path);
        if (n.children) collect(n.children);
      }
    };
    collect(fileTree);
    const validTabs = saved.openTabs.filter((t) => validPaths.has(t.path));
    if (saved.activeTab && validPaths.has(saved.activeTab)) {
      const name = saved.activeTab.split('/').pop() ?? saved.activeTab;
      const tab = { path: saved.activeTab, name };
      const tabs = validTabs.some((t) => t.path === saved.activeTab)
        ? validTabs
        : [tab, ...validTabs];
      setOpenTabs(tabs);
      setActiveTab(saved.activeTab);
      setSelectedFile(saved.activeTab);
    } else if (validTabs.length > 0) {
      setOpenTabs(validTabs);
    }
    setViewMode(saved.viewMode);
    setSidebarVisible(saved.sidebarVisible);
    if (saved.cursorStates) {
      cursorStatesRef.current = saved.cursorStates;
    }
  }, [workspaceMode, fileTree]);

  // Persist on change (debounced)
  useEffect(() => {
    if (workspaceMode !== 'project') return;
    if (persistTimeoutRef.current) clearTimeout(persistTimeoutRef.current);
    persistTimeoutRef.current = setTimeout(() => {
      saveIDEState({
        projectId: PROJECT_ID,
        activeTab,
        openTabs,
        viewMode,
        sidebarVisible,
        cursorStates: cursorStatesRef.current,
      });
      persistTimeoutRef.current = null;
    }, PERSIST_DEBOUNCE_MS);
    return () => {
      if (persistTimeoutRef.current) clearTimeout(persistTimeoutRef.current);
    };
  }, [workspaceMode, activeTab, openTabs, viewMode, sidebarVisible]);

  useEffect(() => {
    if (workspaceMode === 'empty') {
      setFileTree([]);
      setFileContents({});
      setOpenTabs([]);
      setSelectedFile(null);
      setActiveTab('');
      setProject(null);
      setPreviewUrl(null);
      hasRestoredRef.current = false;
    }
  }, [workspaceMode, setProject]);

  // Start preview when switching to App tab with project loaded
  useEffect(() => {
    if (viewMode === 'viewer' && workspaceMode === 'project') {
      startPreview(PROJECT_ID)
        .then((r) => {
          setPreviewUrl(r.url);
          if (!r.ready && r.error) {
            addActivity('Preview failed', r.error, false);
          }
        })
        .catch((e) => {
          setPreviewUrl('http://127.0.0.1:5174');
          addActivity('Preview failed', (e as Error)?.message ?? 'Could not start', false);
        });
    } else {
      setPreviewUrl(null);
    }
  }, [viewMode, workspaceMode, addActivity]);

  const getContent = useCallback((path: string) => fileContents[path] ?? '', [fileContents]);
  const setContent = useCallback((path: string, content: string) => {
    setFileContents((prev) => ({ ...prev, [path]: content }));
  }, []);

  const saveCursorForCurrentFile = useCallback(() => {
    const editor = editorRef.current;
    if (!editor || !activeTab) return;
    try {
      const pos = editor.getPosition();
      const scrollTop = editor.getScrollTop();
      if (pos) {
        cursorStatesRef.current = {
          ...cursorStatesRef.current,
          [activeTab]: { line: pos.lineNumber, column: pos.column, scrollTop },
        };
      }
    } catch {
      // ignore
    }
  }, [activeTab]);

  const openFile = useCallback(
    (path: string, name: string) => {
      saveCursorForCurrentFile();
      setSelectedFile(path);
      setActiveTab(path);
      setOpenTabs((prev) =>
        prev.some((t) => t.path === path) ? prev : [...prev, { path, name }]
      );
    },
    [saveCursorForCurrentFile]
  );

  useEffect(() => {
    if (!activeTab || workspaceMode !== 'project') return;
    getFileContent(PROJECT_ID, activeTab)
      .then((r) =>
        setFileContents((prev) => (prev[activeTab] !== undefined ? prev : { ...prev, [activeTab]: r.content }))
      )
      .catch(() => {});
  }, [activeTab, workspaceMode]);

  const closeTab = useCallback(
    (path: string, e: React.MouseEvent) => {
      e.stopPropagation();
      if (activeTab === path) {
        saveCursorForCurrentFile();
      }
      const idx = openTabs.findIndex((t) => t.path === path);
      const next = openTabs.filter((t) => t.path !== path);
      setOpenTabs(next);
      if (activeTab === path && next.length > 0) {
        const newActive = next[Math.max(0, idx - 1)];
        setActiveTab(newActive.path);
        setSelectedFile(newActive.path);
      } else if (next.length === 0) {
        setActiveTab('');
        setSelectedFile(null);
      }
    },
    [activeTab, openTabs, saveCursorForCurrentFile]
  );

  const content = activeTab ? getContent(activeTab) : '';
  const onContentChange = (value: string) => {
    if (activeTab) setContent(activeTab, value);
  };

  const isEmptyWorkspace = workspaceMode === 'empty';
  const displayFileTree = fileTree.length > 0 ? fileTree : [{ name: 'app', type: 'folder' as const, children: [] }];
  const allFiles = collectFilesFromTree(displayFileTree);

  const handlePublish = useCallback(async () => {
    if (workspaceMode !== 'project') return;
    setPublishLoading(true);
    try {
      const res = await executeCommand(PROJECT_ID, 'npm run build');
      addActivity(res.success ? 'Build completed' : 'Build failed', res.output, res.success);
    } catch (e) {
      addActivity('Build failed', (e as Error)?.message, false);
    } finally {
      setPublishLoading(false);
    }
  }, [workspaceMode, addActivity]);

  const commands = [
    { id: 'editor', label: 'Switch to Editor', run: () => setViewMode('editor') },
    { id: 'app', label: 'Switch to App', run: () => setViewMode('viewer') },
    { id: 'sidebar', label: 'Toggle Sidebar', run: () => setSidebarVisible((v) => !v) },
    { id: 'terminal', label: 'Switch to Terminal', run: () => setViewMode('terminal') },
    { id: 'split', label: 'Toggle Split Editor', run: () => setSplitEditor((v) => !v) },
    { id: 'build', label: 'Build Project', run: handlePublish },
  ];

  const handleBeforeMount = useCallback((monacoInstance: typeof monaco) => {
    monacoInstance.editor.defineTheme('atoms-dark', ATOMS_DARK_THEME as monaco.editor.IStandaloneThemeData);
    monacoInstance.editor.setTheme('atoms-dark');
  }, []);

  const handleEditorMount = useCallback(
    (editor: Monaco.editor.IStandaloneCodeEditor) => {
      editorRef.current = editor;
      const state = cursorStatesRef.current[activeTab];
      if (state) {
        try {
          editor.setPosition({ lineNumber: state.line, column: state.column });
          editor.revealLineInCenter(state.line);
        } catch {
          // ignore
        }
      }
      editor.focus();
    },
    [activeTab]
  );

  return (
    <div
      className="h-screen w-full flex flex-col overflow-hidden text-white relative"
      style={{
        background: "var(--atoms-deep-black)",
        color: "var(--atoms-pearl-white)",
      }}
    >
      <AtomsTopBar
        view={viewMode === 'viewer' ? 'app' : viewMode === 'terminal' ? 'terminal' : 'editor'}
        setView={(v) => setViewMode(v === 'app' ? 'viewer' : v === 'terminal' ? 'terminal' : 'editor')}
        sidebarVisible={sidebarVisible}
        onToggleSidebar={() => setSidebarVisible((v) => !v)}
        onPublish={handlePublish}
        projectName={project?.name ?? (displayFileTree[0]?.name && displayFileTree[0].name !== 'app' ? displayFileTree[0].name : project?.id ?? 'New Project')}
      />

      <div className="flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden">
        <div className="flex-1 flex min-h-0 min-w-0 overflow-hidden">
        {sidebarVisible ? (
          <Group orientation="horizontal" className="flex-1 min-w-0 min-h-0">
            {/* Chat panel - resizable */}
            <Panel
              defaultSize="35"
              minSize="20"
              maxSize="50"
              className="flex flex-col min-h-0"
              style={{ background: '#1a1a1a' }}
            >
              <div className="flex-1 flex flex-col min-h-0 overflow-hidden border-r border-[#2a2a2a]">
                <AtomsChatPanel embedded />
              </div>
            </Panel>
            <Separator className="w-2 bg-[#2a2a2a] hover:bg-[#3a3a3a] data-[resize-handle-active]:bg-[#0e639c] transition-colors" />
            {/* File explorer - resizable */}
            <Panel
              defaultSize="25"
              minSize="15"
              maxSize="40"
              className="flex flex-col min-h-0"
              style={{ background: '#1a1a1a' }}
            >
              <div className="flex-1 flex flex-col min-h-0 overflow-hidden border-r border-[#2a2a2a]">
                <AtomsFileExplorer
                  tree={fileTree.length > 0 ? fileTree.map(fileNodeToExplorerNode) : undefined}
                  selected={selectedFile}
                  onSelect={openFile}
                />
              </div>
            </Panel>
            <Separator className="w-2 bg-[#2a2a2a] hover:bg-[#3a3a3a] data-[resize-handle-active]:bg-[#0e639c] transition-colors" />
            {/* Editor panel - resizable */}
            <Panel
              defaultSize="40"
              minSize="25"
              className="flex flex-col min-h-0 min-w-0"
              style={{ background: '#0d0d0d' }}
            >
              <div className="flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden">
          <div className={cn('flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden relative', (viewMode === 'viewer' || viewMode === 'terminal') && 'hidden')}>
            {/* Tab bar or path bar when empty */}
            <div className="h-9 flex items-center px-2 shrink-0" style={{ background: "var(--atoms-charcoal-light)", borderBottom: "1px solid var(--atoms-sidebar-border)" }}>
              {!activeTab && openTabs.length === 0 && (
                <>
                  <span className="text-[13px] text-[#e5e5e5]">&gt; app</span>
                  <ChevronRight size={14} className="text-[#9a9a9a] ml-0.5" />
                  <div className="flex-1" />
                  <button className="w-7 h-7 rounded hover:bg-[#333] flex items-center justify-center" aria-label="Open in new window">
                    <ExternalLink size={14} className="text-[#9a9a9a]" />
                  </button>
                </>
              )}
              {openTabs.map((tab) => (
                <div
                  key={tab.path}
                  className={cn(
                    'flex items-center gap-1 px-2 py-1 rounded text-xs cursor-pointer',
                    activeTab === tab.path ? 'bg-[#1e1e1e]' : 'hover:bg-[#333]'
                  )}
                  style={{ color: activeTab === tab.path ? "var(--atoms-pearl-white)" : "var(--atoms-text-muted)" }}
                  onClick={() => {
                    if (tab.path !== activeTab) {
                      saveCursorForCurrentFile();
                      setActiveTab(tab.path);
                      setSelectedFile(tab.path);
                    }
                  }}
                >
                  <span className="text-[11px] text-[#6b6b6b]">{getFileExt(tab.name)}</span>
                  <span>{tab.name}</span>
                  <button
                    onClick={(e) => closeTab(tab.path, e)}
                    className="ml-1 hover:bg-[#333] rounded p-0.5"
                    aria-label={`Close ${tab.name}`}
                  >
                    <X className="w-3 h-3 text-[#6b6b6b]" />
                  </button>
                </div>
              ))}
            </div>

            {/* Editor area */}
            <div className="flex-1 min-w-0 overflow-hidden relative flex" style={{ background: "var(--atoms-editor-bg)" }}>
              {!activeTab && (
                <div className="atoms-empty">Select a file</div>
              )}
              {!activeTab ? null : splitEditor ? (
                <>
                  <div className="flex-1 min-w-0 overflow-hidden border-r" style={{ borderColor: '#2a2a2a' }}>
                    {(() => {
                      const diff = pendingDiffs.find((d) => d.filePath === activeTab && d.status === 'pending');
                      if (diff) {
                        return (
                          <DiffReviewEditor
                            filePath={diff.filePath}
                            fileName={diff.fileName}
                            original={diff.original}
                            proposed={diff.proposed}
                            language={diff.fileName.endsWith('.tsx') ? 'typescript' : diff.fileName.endsWith('.ts') ? 'typescript' : 'plaintext'}
                            onAccept={async () => {
                              resolveDiff(activeTab, 'accepted');
                              try {
                                await applyChange(PROJECT_ID, activeTab, diff.proposed);
                                setContent(activeTab, diff.proposed);
                                addActivity('Accepted AI edit', diff.fileName, true);
                              } catch (e) {
                                addActivity('Apply failed', (e as Error)?.message, false);
                              }
                            }}
                            onReject={() => {
                              resolveDiff(activeTab, 'rejected');
                              addActivity('Rejected AI edit', diff.fileName, false);
                            }}
                            onEditThenAccept={() => {
                              resolveDiff(activeTab, 'edited');
                              setContent(activeTab, diff.proposed);
                              addActivity('Editing AI proposal', diff.fileName);
                            }}
                          />
                        );
                      }
                      return (
                        <Editor
                          key={`${activeTab}-split-l`}
                          height="100%"
                          language={activeTab.match(/\.(tsx?|jsx?|json|css|html|md)$/)?.[1] ?? 'plaintext'}
                          value={content}
                          onChange={(v) => onContentChange(v ?? '')}
                          theme="atoms-dark"
                          beforeMount={handleBeforeMount}
                          onMount={handleEditorMount}
                          options={ATOMS_MONACO_OPTIONS as Parameters<typeof Editor>[0]['options']}
                        />
                      );
                    })()}
                  </div>
                  <div className="flex-1 min-w-0 overflow-hidden">
                    {(() => {
                      const diff = pendingDiffs.find((d) => d.filePath === activeTab && d.status === 'pending');
                      if (diff) {
                        return (
                          <DiffReviewEditor
                            filePath={diff.filePath}
                            fileName={diff.fileName}
                            original={diff.original}
                            proposed={diff.proposed}
                            language={diff.fileName.endsWith('.tsx') ? 'typescript' : diff.fileName.endsWith('.ts') ? 'typescript' : 'plaintext'}
                            onAccept={async () => {
                              resolveDiff(activeTab, 'accepted');
                              try {
                                await applyChange(PROJECT_ID, activeTab, diff.proposed);
                                setContent(activeTab, diff.proposed);
                                addActivity('Accepted AI edit', diff.fileName, true);
                              } catch (e) {
                                addActivity('Apply failed', (e as Error)?.message, false);
                              }
                            }}
                            onReject={() => {
                              resolveDiff(activeTab, 'rejected');
                              addActivity('Rejected AI edit', diff.fileName, false);
                            }}
                            onEditThenAccept={() => {
                              resolveDiff(activeTab, 'edited');
                              setContent(activeTab, diff.proposed);
                              addActivity('Editing AI proposal', diff.fileName);
                            }}
                          />
                        );
                      }
                      return (
                        <Editor
                          key={`${activeTab}-split-r`}
                          height="100%"
                          language={activeTab.match(/\.(tsx?|jsx?|json|css|html|md)$/)?.[1] ?? 'plaintext'}
                          value={content}
                          onChange={(v) => onContentChange(v ?? '')}
                          theme="atoms-dark"
                          beforeMount={handleBeforeMount}
                          options={ATOMS_MONACO_OPTIONS as Parameters<typeof Editor>[0]['options']}
                        />
                      );
                    })()}
                  </div>
                </>
              ) : (() => {
                const diff = pendingDiffs.find((d) => d.filePath === activeTab && d.status === 'pending');
                if (diff) {
                  return (
                    <DiffReviewEditor
                      filePath={diff.filePath}
                      fileName={diff.fileName}
                      original={diff.original}
                      proposed={diff.proposed}
                      language={diff.fileName.endsWith('.tsx') ? 'typescript' : diff.fileName.endsWith('.ts') ? 'typescript' : 'plaintext'}
                      onAccept={async () => {
                        resolveDiff(activeTab, 'accepted');
                        try {
                          await applyChange(PROJECT_ID, activeTab, diff.proposed);
                          setContent(activeTab, diff.proposed);
                          addActivity('Accepted AI edit', diff.fileName, true);
                        } catch (e) {
                          addActivity('Apply failed', (e as Error)?.message, false);
                        }
                      }}
                      onReject={() => {
                        resolveDiff(activeTab, 'rejected');
                        addActivity('Rejected AI edit', diff.fileName, false);
                      }}
                      onEditThenAccept={() => {
                        resolveDiff(activeTab, 'edited');
                        setContent(activeTab, diff.proposed);
                        addActivity('Editing AI proposal', diff.fileName);
                      }}
                    />
                  );
                }
                return (
                  <Editor
                    key={activeTab}
                    height="100%"
                    language={activeTab.match(/\.(tsx?|jsx?|json|css|html|md)$/)?.[1] ?? 'plaintext'}
                    value={content}
                    onChange={(v) => onContentChange(v ?? '')}
                    theme="atoms-dark"
                    beforeMount={handleBeforeMount}
                    onMount={handleEditorMount}
                    options={ATOMS_MONACO_OPTIONS as Parameters<typeof Editor>[0]['options']}
                  />
                );
              })()}
            </div>
          </div>

          <div className={cn('flex-1 min-h-0 min-w-0 overflow-hidden', (viewMode === 'editor' || viewMode === 'terminal') && 'hidden')}>
            <iframe
              src={previewUrl || 'about:blank'}
              title="App Viewer"
              className="h-full w-full border-0"
              style={{ background: '#1e1e1e' }}
            />
          </div>
          <div className={cn('flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden', viewMode !== 'terminal' && 'hidden')}>
            <AtomsTerminalPanel />
          </div>
              </div>
            </Panel>
          </Group>
        ) : (
        <div className="flex-1 flex flex-col overflow-hidden min-w-0 min-h-0" style={{ background: "var(--atoms-editor-bg)" }}>
          <div className={cn('flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden relative', (viewMode === 'viewer' || viewMode === 'terminal') && 'hidden')}>
            {/* Tab bar or path bar when empty */}
            <div className="h-9 flex items-center px-2 shrink-0" style={{ background: "var(--atoms-charcoal-light)", borderBottom: "1px solid var(--atoms-sidebar-border)" }}>
              {!activeTab && openTabs.length === 0 && (
                <>
                  <span className="text-[13px] text-[#e5e5e5]">&gt; app</span>
                  <ChevronRight size={14} className="text-[#9a9a9a] ml-0.5" />
                  <div className="flex-1" />
                  <button className="w-7 h-7 rounded hover:bg-[#333] flex items-center justify-center" aria-label="Open in new window">
                    <ExternalLink size={14} className="text-[#9a9a9a]" />
                  </button>
                </>
              )}
              {openTabs.map((tab) => (
                <div
                  key={tab.path}
                  className={cn(
                    'flex items-center gap-1 px-2 py-1 rounded text-xs cursor-pointer',
                    activeTab === tab.path ? 'bg-[#1e1e1e]' : 'hover:bg-[#333]'
                  )}
                  style={{ color: activeTab === tab.path ? "var(--atoms-pearl-white)" : "var(--atoms-text-muted)" }}
                  onClick={() => {
                    if (tab.path !== activeTab) {
                      saveCursorForCurrentFile();
                      setActiveTab(tab.path);
                      setSelectedFile(tab.path);
                    }
                  }}
                >
                  <span className="text-[11px] text-[#6b6b6b]">{getFileExt(tab.name)}</span>
                  <span>{tab.name}</span>
                  <button
                    onClick={(e) => closeTab(tab.path, e)}
                    className="ml-1 hover:bg-[#333] rounded p-0.5"
                    aria-label={`Close ${tab.name}`}
                  >
                    <X className="w-3 h-3 text-[#6b6b6b]" />
                  </button>
                </div>
              ))}
            </div>
            <div className="flex-1 min-w-0 overflow-hidden relative flex" style={{ background: "var(--atoms-editor-bg)" }}>
              {!activeTab && (
                <div className="atoms-empty">Select a file</div>
              )}
              {!activeTab ? null : (() => {
                const diff = pendingDiffs.find((d) => d.filePath === activeTab && d.status === 'pending');
                if (diff) {
                  return (
                    <DiffReviewEditor
                      filePath={diff.filePath}
                      fileName={diff.fileName}
                      original={diff.original}
                      proposed={diff.proposed}
                      language={diff.fileName.endsWith('.tsx') ? 'typescript' : diff.fileName.endsWith('.ts') ? 'typescript' : 'plaintext'}
                      onAccept={async () => {
                        resolveDiff(activeTab, 'accepted');
                        try {
                          await applyChange(PROJECT_ID, activeTab, diff.proposed);
                          setContent(activeTab, diff.proposed);
                          addActivity('Accepted AI edit', diff.fileName, true);
                        } catch (e) {
                          addActivity('Apply failed', (e as Error)?.message, false);
                        }
                      }}
                      onReject={() => {
                        resolveDiff(activeTab, 'rejected');
                        addActivity('Rejected AI edit', diff.fileName, false);
                      }}
                      onEditThenAccept={() => {
                        resolveDiff(activeTab, 'edited');
                        setContent(activeTab, diff.proposed);
                        addActivity('Editing AI proposal', diff.fileName);
                      }}
                    />
                  );
                }
                return (
                  <Editor
                    key={activeTab}
                    height="100%"
                    language={activeTab.match(/\.(tsx?|jsx?|json|css|html|md)$/)?.[1] ?? 'plaintext'}
                    value={content}
                    onChange={(v) => onContentChange(v ?? '')}
                    theme="atoms-dark"
                    beforeMount={handleBeforeMount}
                    onMount={handleEditorMount}
                    options={ATOMS_MONACO_OPTIONS as Parameters<typeof Editor>[0]['options']}
                  />
                );
              })()}
            </div>
          </div>
          <div className={cn('flex-1 min-h-0 min-w-0 overflow-hidden', (viewMode === 'editor' || viewMode === 'terminal') && 'hidden')}>
            <iframe
              src={previewUrl || 'about:blank'}
              title="App Viewer"
              className="h-full w-full border-0"
              style={{ background: '#1e1e1e' }}
            />
          </div>
          <div className={cn('flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden', viewMode !== 'terminal' && 'hidden')}>
            <AtomsTerminalPanel />
          </div>
        </div>
        )}
        </div>
      </div>

      <AIIntentPanel />
      <IntentPreviewPanel onApprovePlan={executeApprovedPlan} />
      <DiffReviewPanel onApproveDiff={applyApprovedDiffPlan} />

      {quickOpenMode && (
        <AtomsQuickOpen
          mode={quickOpenMode}
          onClose={() => setQuickOpenMode(null)}
          files={allFiles}
          commands={commands}
          onOpenFile={openFile}
        />
      )}
    </div>
  );
}
