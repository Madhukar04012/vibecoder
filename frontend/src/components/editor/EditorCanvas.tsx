/**
 * EditorCanvas - Monaco Editor (READ-ONLY)
 * ATMOS mode: AI writes code, user reads it
 *
 * Uses `value` prop for reliable content syncing (controlled mode).
 * Language switching is imperative to avoid full remounts.
 * Auto-scrolls to bottom during live writing for Cursor-style effect.
 */

import { useRef, useEffect, useCallback } from "react";
import Editor, { type OnMount } from "@monaco-editor/react";
import { useIDEStore } from "@/stores/ide-store";
import { Loader2, Sparkles } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";

interface EditorCanvasProps {
  file?: string | null;
}

const LANG_MAP: Record<string, string> = {
  ts: "typescript", tsx: "typescript", js: "javascript", jsx: "javascript",
  py: "python", json: "json", css: "css", html: "html", md: "markdown",
  yml: "yaml", yaml: "yaml", sh: "shell", bash: "shell",
  sql: "sql", rs: "rust", go: "go", java: "java", rb: "ruby",
  php: "php", c: "c", cpp: "cpp", h: "c", hpp: "cpp",
  swift: "swift", kt: "kotlin", dart: "dart", r: "r",
  xml: "xml", svg: "xml", toml: "toml", ini: "ini",
  dockerfile: "dockerfile", makefile: "makefile",
  graphql: "graphql", prisma: "prisma", txt: "plaintext",
};

function getLanguage(path: string): string {
  const name = path.split("/").pop()?.toLowerCase() || "";
  if (name === "dockerfile") return "dockerfile";
  if (name === "makefile") return "makefile";
  if (name === ".env" || name === ".env.example") return "ini";
  const ext = name.split(".").pop() || "";
  return LANG_MAP[ext] || "plaintext";
}

export function EditorCanvas({ file }: EditorCanvasProps) {
  const storeActiveFile = useIDEStore((s) => s.activeFile);
  const activeFile = file ?? storeActiveFile;
  const aiCurrentFile = useIDEStore((s) => s.aiCurrentFile);
  const aiStatus = useIDEStore((s) => s.aiStatus);
  const { resolvedTheme } = useTheme();

  // Subscribe to file content reactively — selector uses activeFile from render
  const content = useIDEStore((s) =>
    activeFile ? s.fileContents[activeFile] ?? "" : ""
  );

  // Subscribe only to the active file's live-writing status, not the whole object
  const isLiveWriting = useIDEStore((s) =>
    activeFile ? Boolean(s.fileLiveWriting[activeFile]) : false
  );

  const editorRef = useRef<any>(null);
  const monacoRef = useRef<any>(null);
  const currentFileRef = useRef<string | null>(null);
  const isAIFile = aiStatus === 'generating' && aiCurrentFile === activeFile;

  // ── Switch language when active file changes (imperative, no remount) ──
  useEffect(() => {
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    if (!editor || !monaco || !activeFile) return;

    if (currentFileRef.current !== activeFile) {
      const model = editor.getModel();
      if (model) {
        const lang = getLanguage(activeFile);
        monaco.editor.setModelLanguage(model, lang);
      }
      currentFileRef.current = activeFile;
    }
  }, [activeFile]);

  // ── Auto-scroll to bottom during live writing ──
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor || !isLiveWriting) return;

    const model = editor.getModel();
    if (!model) return;

    const lastLine = model.getLineCount();
    editor.revealLine(lastLine, 1);
    const lastCol = model.getLineMaxColumn(lastLine);
    editor.setPosition({ lineNumber: lastLine, column: lastCol });
  }, [content, isLiveWriting]);

  // ── Change theme without remount ──
  useEffect(() => {
    if (monacoRef.current) {
      monacoRef.current.editor.setTheme(resolvedTheme === 'dark' ? 'vs-dark' : 'vs');
    }
  }, [resolvedTheme]);

  const handleMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    currentFileRef.current = null;
  }, []);

  if (!activeFile) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-6" style={{ background: 'var(--ide-bg-deep)' }}>
        <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 flex items-center justify-center border border-blue-500/20">
          <Sparkles size={40} className="text-blue-400/60" />
        </div>
        <div className="text-center">
          <p className="text-[16px] font-medium mb-2" style={{ color: 'var(--ide-text)' }}>AI will write code here</p>
          <p className="text-[13px]" style={{ color: 'var(--ide-text-muted)' }}>Select a file or start a conversation to begin</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 min-h-0 min-w-0 overflow-hidden relative" style={{ position: 'relative', height: '100%', width: '100%' }}>
      {/* Live writing overlay */}
      {(isLiveWriting || isAIFile) && (
        <div className="absolute top-3 right-4 z-10 flex items-center gap-3 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600/25 to-purple-600/25 border border-blue-500/30 backdrop-blur-md shadow-lg shadow-blue-500/10">
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-blue-400 animate-pulse" />
            <span className="text-[13px] font-medium text-blue-200">AI is writing code</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="w-1 h-1 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1 h-1 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1 h-1 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>
      )}

      {/* Absolute-positioned wrapper ensures Monaco always has computed dimensions */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}>
        <Editor
          height="100%"
          width="100%"
          theme={resolvedTheme === 'dark' ? 'vs-dark' : 'vs'}
          language={activeFile ? getLanguage(activeFile) : 'plaintext'}
          value={content}
          onMount={handleMount}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Menlo, Monaco, monospace",
            fontLigatures: true,
            lineHeight: 20,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            padding: { top: 12, bottom: 12 },
            renderLineHighlight: 'line',
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
            smoothScrolling: true,
            bracketPairColorization: { enabled: true },
            guides: { bracketPairs: true, indentation: true },
            wordWrap: 'on',
            readOnly: true,
            tabSize: 2,
            suggest: { showWords: false },
            overviewRulerBorder: false,
            scrollbar: {
              verticalScrollbarSize: 8,
              horizontalScrollbarSize: 8,
              verticalSliderSize: 8,
            },
          }}
          loading={
            <div className="flex items-center justify-center h-full gap-2 text-[13px]" style={{ color: 'var(--ide-text-muted)' }}>
              <Loader2 size={14} className="animate-spin" />
              Loading editor...
            </div>
          }
        />
      </div>
    </div>
  );
}
