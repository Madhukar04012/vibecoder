/**
 * IDE bridge — connects window.ideAPI to the IDE store.
 * Tools (read_file, write_file, list_files, run_terminal, open_file_in_editor) use this.
 */

import type { useIDEStore } from "@/stores/ide-store";
import { getApiUrl } from "@/lib/api";
import { getStoredToken } from "@/lib/auth-storage";

type IDEStoreState = ReturnType<typeof useIDEStore.getState>;

export function installIdeAPI(getState: () => IDEStoreState): void {
  const normalizePath = (p: string) => p.replace(/^\/workspace\/?/, "").replace(/^\//, "") || p;

  window.ideAPI = {
    readFile: async (path: string) => {
      const state = getState();
      const keys = Object.keys(state.fileContents);
      const normalized = normalizePath(path);
      const match = keys.find((k) => k === path || k === normalized || k.endsWith("/" + normalized) || k.endsWith(path));
      return state.fileContents[match ?? normalized ?? path] ?? "";
    },

    writeFile: async (path: string, content: string) => {
      const state = getState();
      const p = normalizePath(path) || path;
      const exists = p in state.fileContents;
      if (exists) {
        state.updateFileContent(p, content);
      } else {
        state.createFile(p, content, true);
      }
    },

    listFiles: async (path?: string) => {
      const state = getState();
      const keys = Object.keys(state.fileContents);
      if (!path) return keys;
      const prefix = normalizePath(path);
      if (!prefix) return keys;
      const withSlash = prefix.endsWith("/") ? prefix : `${prefix}/`;
      return keys.filter((k) => k === prefix || k.startsWith(withSlash));
    },

    runCommand: async (command: string) => {
      const state = getState();
      state.appendTerminalLine(`$ ${command}`, "command");

      try {
        const token = getStoredToken();
        const projectId = state.project?.id ?? "workspace";
        const res = await fetch(getApiUrl("studio/execute"), {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            command,
            project_id: projectId,
          }),
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const stdout = data.stdout ?? data.output ?? "";
        const stderr = data.stderr ?? data.error ?? "";

        if (stdout) state.appendTerminalLine(stdout, "stdout");
        if (stderr) state.appendTerminalLine(stderr, "stderr");

        return { stdout, stderr };
      } catch (err) {
        // Fallback: if backend not reachable, show error but don't crash
        const errMsg = err instanceof Error ? err.message : String(err);
        state.appendTerminalLine(`Error: ${errMsg}`, "stderr");
        return { stdout: "", stderr: errMsg };
      }
    },

    openFile: (path: string) => {
      const state = getState();
      const p = normalizePath(path) || path;
      const keys = Object.keys(state.fileContents);
      const match = keys.find((k) => k === p || k.endsWith(p));
      state.openFile(match ?? p);
    },

    refreshFileTree: () => {
      // File tree is reactive from fileContents; no-op.
    },
  };
}

export function uninstallIdeAPI(): void {
  delete (window as { ideAPI?: unknown }).ideAPI;
}
