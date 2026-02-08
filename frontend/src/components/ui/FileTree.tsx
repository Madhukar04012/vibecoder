/**
 * FileTree - Re-export from FilePanel
 * Legacy compatibility - the FilePanel now handles all tree rendering.
 */

export interface FileNode {
  id: string;
  name: string;
  path: string;
  type: "file" | "folder";
  children?: FileNode[];
}

// Re-export for backward compatibility
export { default as FileTree } from "@/components/layout/FilePanel";
