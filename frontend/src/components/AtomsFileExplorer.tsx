import { useState } from "react";
import { ChevronRight, FileCode, FolderTree } from "lucide-react";
import { cn } from "@/lib/utils";

export interface FileExplorerNode {
  name: string;
  type: "file" | "folder";
  path?: string;
  children?: FileExplorerNode[];
}

const DEFAULT_TREE: FileExplorerNode[] = [
  {
    name: "app",
    type: "folder",
    children: [
      {
        name: "frontend",
        type: "folder",
        children: [
          { name: ".mgx", type: "folder", children: [] },
          { name: "dist", type: "folder", children: [] },
          { name: "public", type: "folder", children: [] },
          { name: "seo-scripts", type: "folder", children: [] },
          {
            name: "src",
            type: "folder",
            children: [
              {
                name: "components",
                type: "folder",
                children: [
                  { name: "AuthModal.tsx", type: "file", path: "app/frontend/src/components/AuthModal.tsx" },
                  { name: "Community.tsx", type: "file", path: "app/frontend/src/components/Community.tsx" },
                  { name: "FanArtUpload.tsx", type: "file", path: "app/frontend/src/components/FanArtUpload.tsx" },
                  { name: "Footer.tsx", type: "file", path: "app/frontend/src/components/Footer.tsx" },
                  { name: "GallerySection.tsx", type: "file", path: "app/frontend/src/components/GallerySection.tsx" },
                  { name: "HeroSection.tsx", type: "file", path: "app/frontend/src/components/HeroSection.tsx" },
                  { name: "MoviesSection.tsx", type: "file", path: "app/frontend/src/components/MoviesSection.tsx" },
                  { name: "MusicPlayer.tsx", type: "file", path: "app/frontend/src/components/MusicPlayer.tsx" },
                  { name: "Navigation.tsx", type: "file", path: "app/frontend/src/components/Navigation.tsx" },
                  { name: "NewsSection.tsx", type: "file", path: "app/frontend/src/components/NewsSection.tsx" },
                  { name: "RecordsSection.tsx", type: "file", path: "app/frontend/src/components/RecordsSection.tsx" },
                  { name: "StyleSection.tsx", type: "file", path: "app/frontend/src/components/StyleSection.tsx" },
                ],
              },
              { name: "ui", type: "folder", children: [] },
            ],
          },
          { name: "data", type: "folder", children: [] },
          { name: "hooks", type: "folder", children: [] },
        ],
      },
    ],
  },
];

function FileExplorerItem({
  node,
  level,
  selected,
  onSelect,
  forceOpen,
}: {
  node: FileExplorerNode;
  level: number;
  selected: string | null;
  onSelect: (path: string, name: string) => void;
  forceOpen?: boolean;
}) {
  const [open, setOpen] = useState(forceOpen ?? level < 3);
  const isFolder = node.type === "folder";
  const hasChildren = isFolder && node.children && node.children.length > 0;
  const isSelected = selected === (node.path || node.name);

  if (isFolder) {
    return (
      <div className="select-none" style={{ animationDelay: `${level * 30}ms` }}>
        <div
          className="atoms-tree-item flex items-center gap-1 text-[#e3e3e3] hover:bg-[#333] cursor-pointer transition-colors duration-150 rounded-sm px-1 -mx-1"
          style={{ paddingLeft: `${level * 12 + 8}px` }}
          onClick={() => setOpen(!open)}
        >
          {hasChildren ? (
            <span className={cn("shrink-0 transition-transform duration-200", open && "rotate-90")}>
              <ChevronRight className="w-3.5 h-3.5 text-[#8b8b8b]" />
            </span>
          ) : (
            <span className="w-3.5" />
          )}
          <span className="truncate">{node.name}</span>
        </div>
        {hasChildren && open && (
          <div className="overflow-hidden animate-fade-in">
            {node.children!.map((child, i) => (
              <FileExplorerItem
                key={child.name + i}
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
        "atoms-tree-item flex items-center gap-1.5 cursor-pointer rounded-sm px-1 -mx-1 transition-all duration-150",
        isSelected ? "bg-[#3a3a3a] text-white" : "text-[#e3e3e3] hover:bg-[#333]"
      )}
      style={{ paddingLeft: `${level * 12 + 24}px` }}
      onClick={() => onSelect(node.path || node.name, node.name)}
    >
      <FileCode size={14} className="text-[#8b8b8b] shrink-0 transition-colors duration-150" />
      <span className="truncate">{node.name}</span>
    </div>
  );
}

export function AtomsFileExplorer({
  tree,
  selected,
  onSelect,
}: {
  tree?: FileExplorerNode[] | null;
  selected: string | null;
  onSelect: (path: string, name: string) => void;
}) {
  const nodes = tree && tree.length > 0 ? tree : DEFAULT_TREE;

  return (
    <div
      className="flex flex-col h-full w-full min-w-0 min-h-0 overflow-hidden"
      style={{ background: 'var(--atoms-sidebar-bg)' }}
    >
      <div className="shrink-0 px-3 py-2 flex items-center gap-2 text-[13px] text-[#9a9a9a] border-b border-[#252525]">
        <FolderTree size={14} className="text-[#6b6b6b]" />
        <span>Files</span>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden py-2 overscroll-contain">
        {nodes.map((node, i) => (
          <FileExplorerItem
            key={node.name + i}
            node={node}
            level={0}
            selected={selected}
            onSelect={onSelect}
            forceOpen={i === 0}
          />
        ))}
      </div>
    </div>
  );
}

