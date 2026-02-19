/**
 * IDE tools — bridge between agents and the real IDE.
 * read_file, write_file, list_files, run_terminal, open_file_in_editor.
 */

export interface Tool {
  name: string;
  description: string;
  execute: (params: Record<string, unknown>) => Promise<unknown>;
}

declare global {
  interface Window {
    ideAPI?: {
      readFile: (path: string) => Promise<string>;
      writeFile: (path: string, content: string) => Promise<void>;
      listFiles: (path?: string) => Promise<string[]>;
      runCommand: (command: string) => Promise<{ stdout: string; stderr: string }>;
      openFile: (path: string) => void;
      refreshFileTree: () => void;
    };
  }
}

export const IDE_TOOLS: Tool[] = [
  {
    name: "read_file",
    description: "Read a file from the workspace",
    execute: async ({ path }: Record<string, unknown>) => {
      const p = String(path ?? "");
      const content = await window.ideAPI?.readFile(p);
      return { content: content ?? "", path: p };
    },
  },
  {
    name: "write_file",
    description: "Write or create a file in the workspace",
    execute: async ({ path, content }: Record<string, unknown>) => {
      const p = String(path ?? "");
      const c = typeof content === "string" ? content : String(content ?? "");
      await window.ideAPI?.writeFile(p, c);
      window.ideAPI?.refreshFileTree();
      return { success: true, path: p };
    },
  },
  {
    name: "list_files",
    description: "List all files in a directory",
    execute: async ({ path }: Record<string, unknown>) => {
      const dir = (path as string) ?? "/workspace";
      const files = await window.ideAPI?.listFiles(dir);
      return { files: files ?? [] };
    },
  },
  {
    name: "run_terminal",
    description: "Run a terminal command",
    execute: async ({ command }: Record<string, unknown>) => {
      const cmd = String(command ?? "");
      const result = await window.ideAPI?.runCommand(cmd);
      return {
        output: result?.stdout ?? "",
        error: result?.stderr ?? "",
      };
    },
  },
  {
    name: "open_file_in_editor",
    description: "Open a file in the Monaco editor",
    execute: async ({ path }: Record<string, unknown>) => {
      const p = String(path ?? "");
      window.ideAPI?.openFile(p);
      return { success: true };
    },
  },
];
