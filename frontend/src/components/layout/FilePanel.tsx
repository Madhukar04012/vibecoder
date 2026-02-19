/**
 * FilePanel - Professional File Explorer
 * Clean, modern file tree with AI-generated indicators.
 */

import { useMemo } from "react";
import {
  FolderTree, File, FolderOpen, Folder, ChevronRight, ChevronDown,
  Sparkles, Search, FileCode, FileJson, FileText, Braces, Hash,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useIDEStore } from "@/stores/ide-store";
import { useState } from "react";

// ─── Types ──────────────────────────────────────────────────────────────────

interface TreeNode {
  id: string;
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: TreeNode[];
  isNew?: boolean;
  isAIGenerated?: boolean;
}

// ─── Build tree from flat paths ─────────────────────────────────────────────

function buildTree(paths: string[], fileStatuses: Record<string, { isNew: boolean; isAIGenerated: boolean }>): TreeNode[] {
  const root: Record<string, unknown> = {};

  for (const path of paths) {
    const parts = path.split("/").filter(Boolean);
    let node: Record<string, unknown> = root;
    for (const part of parts) {
      if (!node[part]) node[part] = {};
      node = node[part] as Record<string, unknown>;
    }
  }

  let id = 0;
  const convert = (obj: Record<string, unknown>, basePath = ""): TreeNode[] => {
    return Object.entries(obj)
      .sort(([a, aVal], [b, bVal]) => {
        const aIsFolder = Object.keys(aVal as Record<string, unknown>).length > 0;
        const bIsFolder = Object.keys(bVal as Record<string, unknown>).length > 0;
        if (aIsFolder !== bIsFolder) return aIsFolder ? -1 : 1;
        return a.localeCompare(b);
      })
      .map(([name, children]) => {
        const path = basePath ? `${basePath}/${name}` : name;
        const childEntries = Object.keys(children as Record<string, unknown>);
        const isFile = childEntries.length === 0;
        const status = fileStatuses[path];

        return {
          id: `n-${id++}`,
          name,
          path,
          type: isFile ? 'file' : 'folder',
          children: isFile ? undefined : convert(children as Record<string, unknown>, path),
          isNew: status?.isNew,
          isAIGenerated: status?.isAIGenerated,
        } as TreeNode;
      });
  };

  return convert(root);
}

// ─── File Icon ────────────────────────────────────────────────────────────────

const FILE_ICONS: Record<string, { icon: typeof File; color: string }> = {
  ts: { icon: FileCode, color: "#3178c6" },
  tsx: { icon: FileCode, color: "#3178c6" },
  js: { icon: FileCode, color: "#f7df1e" },
  jsx: { icon: FileCode, color: "#f7df1e" },
  py: { icon: FileCode, color: "#3776ab" },
  json: { icon: FileJson, color: "#f59e0b" },
  css: { icon: Hash, color: "#06b6d4" },
  html: { icon: Braces, color: "#f97316" },
  md: { icon: FileText, color: "#6b7280" },
  txt: { icon: FileText, color: "#6b7280" },
  yml: { icon: FileJson, color: "#ef4444" },
  yaml: { icon: FileJson, color: "#ef4444" },
  env: { icon: File, color: "#22c55e" },
};

function FileIcon({ name }: { name: string }) {
  const ext = name.split(".").pop()?.toLowerCase() || "";
  const config = FILE_ICONS[ext] || { icon: File, color: "#6b7280" };
  const IconComp = config.icon;
  return <IconComp size={15} style={{ color: config.color }} />;
}

// ─── Tree Node Component ────────────────────────────────────────────────────

function TreeNodeItem({ node, level }: { node: TreeNode; level: number }) {
  const [open, setOpen] = useState(level < 2);
  const openFile = useIDEStore((s) => s.openFile);
  const activeFile = useIDEStore((s) => s.activeFile);
  const aiCurrentFile = useIDEStore((s) => s.aiCurrentFile);

  const isFolder = node.type === 'folder';
  const isActive = node.path === activeFile;
  const isBeingGenerated = node.path === aiCurrentFile;

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-2 h-[32px] px-2 text-[13px] cursor-pointer select-none transition-all duration-150 rounded-lg mx-1",
          isActive && "bg-blue-500/15 text-blue-300",
          isBeingGenerated && "bg-gradient-to-r from-blue-500/10 to-purple-500/10 animate-pulse",
          node.isNew && !isActive && "text-emerald-400/90",
        )}
        style={{
          paddingLeft: 8 + level * 14,
          ...(!isActive && !node.isNew ? { color: 'var(--ide-text-secondary)' } : {}),
        }}
        onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'var(--ide-surface-hover)'; }}
        onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
        onClick={() => {
          if (isFolder) setOpen((o) => !o);
          else openFile(node.path);
        }}
      >
        {/* Folder chevron */}
        {isFolder ? (
          <div className={cn("w-4 h-4 flex items-center justify-center rounded transition-transform", open && "rotate-90")}>
            <ChevronRight size={14} style={{ color: 'var(--ide-text-muted)' }} />
          </div>
        ) : (
          <span className="w-4 shrink-0" />
        )}

        {/* Icon */}
        {isFolder ? (
          open ? (
            <FolderOpen size={16} className="text-amber-400 shrink-0" />
          ) : (
            <Folder size={16} className="text-amber-400/70 shrink-0" />
          )
        ) : (
          <FileIcon name={node.name} />
        )}

        {/* Name */}
        <span className="truncate flex-1">{node.name}</span>

        {/* AI badge */}
        {node.isAIGenerated && (
          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-blue-500/10 shrink-0">
            <Sparkles size={10} className="text-blue-400" />
          </div>
        )}
        
        {/* Generating indicator */}
        {isBeingGenerated && (
          <div className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse shrink-0" />
        )}
      </div>

      {/* Children */}
      {isFolder && open && node.children && (
        <div className="relative">
          {/* Indent guide line */}
          <div 
            className="absolute top-0 bottom-0 w-px opacity-20"
            style={{ left: 16 + level * 14, background: 'var(--ide-text-muted)' }}
          />
          {node.children.map((child) => (
            <TreeNodeItem key={child.id} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── FilePanel ────────────────────────────────────────────────────────────────

export default function FilePanel() {
  const fileContents = useIDEStore((s) => s.fileContents);
  const fileStatuses = useIDEStore((s) => s.fileStatuses);
  const aiStatus = useIDEStore((s) => s.aiStatus);
  const aiFileProgress = useIDEStore((s) => s.aiFileProgress);

  const tree = useMemo(
    () => buildTree(Object.keys(fileContents), fileStatuses),
    [fileContents, fileStatuses]
  );

  const fileCount = Object.keys(fileContents).length;

  return (
    <div className="flex flex-col h-full w-full min-w-0 min-h-0 overflow-hidden" style={{ background: "var(--ide-panel-bg)" }}>
      {/* Header */}
      <div className="shrink-0 px-4 py-3 flex items-center justify-between" style={{ borderBottom: '1px solid var(--ide-border)' }}>
        <div className="flex items-center gap-2">
          <FolderTree size={16} className="text-blue-400" />
          <span className="text-[12px] font-semibold uppercase tracking-wider" style={{ color: 'var(--ide-text-muted)' }}>Explorer</span>
        </div>
        <div className="flex items-center gap-2">
          {fileCount > 0 && (
            <span className="text-[11px] px-2 py-0.5 rounded-md" style={{ background: 'var(--ide-surface)', color: 'var(--ide-text-muted)' }}>
              {fileCount} files
            </span>
          )}
          {/* AI progress */}
          {aiStatus === 'generating' && aiFileProgress && (
            <span className="text-[11px] text-blue-400 flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-blue-500/10">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
              {aiFileProgress.index}/{aiFileProgress.total}
            </span>
          )}
        </div>
      </div>

      {/* File Tree */}
      <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden py-2 overscroll-contain">
        {tree.length > 0 ? (
          tree.map((node) => (
            <TreeNodeItem key={node.id} node={node} level={0} />
          ))
        ) : (
          <div className="flex flex-col items-center justify-center h-full px-6 text-center">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4" style={{ background: 'var(--ide-surface)' }}>
              <FolderOpen size={28} className="text-zinc-500" />
            </div>
            <p className="text-[14px] font-medium mb-1" style={{ color: 'var(--ide-text)' }}>No files yet</p>
            <p className="text-[12px]" style={{ color: 'var(--ide-text-muted)' }}>Files will appear here when AI generates code</p>
          </div>
        )}
      </div>
    </div>
  );
}
