/**
 * FilePanel - ATMOS Mode: Read-Only File Tree
 * 
 * ATMOS Rules:
 * - NO new file button
 * - NO file creation dialog
 * - Files ONLY appear via AI generation
 * - User can click to VIEW files (read-only)
 */

import { useMemo } from "react";
import {
  FolderTree, File, FolderOpen, Folder, ChevronRight, ChevronDown,
  Sparkles,
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

// ─── File Icon ──────────────────────────────────────────────────────────────

function FileIcon({ name }: { name: string }) {
  const ext = name.split(".").pop()?.toLowerCase() || "";
  const colors: Record<string, string> = {
    ts: "#3178c6", tsx: "#3178c6", js: "#f7df1e", jsx: "#f7df1e",
    py: "#3776ab", json: "#6b7280", css: "#264de4", html: "#e34c26",
    md: "#6b7280", yml: "#cb171e", yaml: "#cb171e", env: "#ecd53f",
    txt: "#6b7280", svg: "#ff9a00", png: "#a855f7", jpg: "#a855f7",
  };
  return <File size={14} style={{ color: colors[ext] || "#6b7280" }} />;
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
          "flex items-center gap-1.5 h-[28px] px-2 text-[12px] cursor-pointer select-none transition-all duration-150",
          isActive && "bg-blue-500/10 text-blue-300",
          !isActive && "text-gray-400 hover:bg-[#1a1a1a] hover:text-gray-300",
          isBeingGenerated && "bg-blue-500/5 animate-pulse",
          node.isNew && !isActive && "text-emerald-400/80",
        )}
        style={{ paddingLeft: 8 + level * 16 }}
        onClick={() => {
          if (isFolder) setOpen((o) => !o);
          else openFile(node.path);
        }}
      >
        {/* Folder chevron */}
        {isFolder ? (
          open ? (
            <ChevronDown size={12} className="text-gray-500 shrink-0" />
          ) : (
            <ChevronRight size={12} className="text-gray-500 shrink-0" />
          )
        ) : (
          <span className="w-3 shrink-0" />
        )}

        {/* Icon */}
        {isFolder ? (
          open ? <FolderOpen size={14} className="text-blue-400/60 shrink-0" /> : <Folder size={14} className="text-gray-500 shrink-0" />
        ) : (
          <FileIcon name={node.name} />
        )}

        {/* Name */}
        <span className="truncate">{node.name}</span>

        {/* AI badge */}
        {node.isAIGenerated && (
          <Sparkles size={10} className="text-blue-400/50 shrink-0 ml-auto" />
        )}
      </div>

      {/* Children */}
      {isFolder && open && node.children && (
        <div>
          {node.children.map((child) => (
            <TreeNodeItem key={child.id} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── FilePanel ──────────────────────────────────────────────────────────────

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
    <div className="flex flex-col h-full w-full min-w-0 min-h-0 overflow-hidden" style={{ background: "#0b0b0b" }}>
      {/* Header — NO new file button */}
      <div className="shrink-0 px-3 py-2 flex items-center gap-2 text-[11px] text-white/60 border-b border-[#1a1a1a]">
        <FolderTree size={13} />
        <span className="font-medium uppercase tracking-wider">Explorer</span>
        {fileCount > 0 && (
          <span className="ml-auto text-white/30">{fileCount}</span>
        )}

        {/* AI progress */}
        {aiStatus === 'generating' && (
          <span className="text-[10px] text-blue-400 flex items-center gap-1">
            <span className="w-1 h-1 rounded-full bg-blue-400 animate-pulse" />
            {aiFileProgress.current}/{aiFileProgress.total}
          </span>
        )}
      </div>

      {/* Tree — view only, no create/rename/delete */}
      <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden py-1 overscroll-contain">
        {tree.length > 0 ? (
          tree.map((node) => (
            <TreeNodeItem key={node.id} node={node} level={0} />
          ))
        ) : (
          <div className="flex flex-col items-center justify-center h-full px-4 text-center">
            <div className="text-white/20 mb-2">
              <FolderOpen size={28} strokeWidth={1.5} />
            </div>
            <p className="text-[12px] text-white/40">No files yet</p>
          </div>
        )}
      </div>
    </div>
  );
}
