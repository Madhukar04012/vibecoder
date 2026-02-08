/**
 * EditorCanvas - Monaco Editor with LIVE code writing
 * Characters appear one by one as the AI types them — Cursor-style
 */

import { useRef, useEffect } from "react";
import Editor, { type OnMount } from "@monaco-editor/react";
import { useIDEStore } from "@/stores/ide-store";
import { Loader2, Sparkles } from "lucide-react";

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
  const fileStatuses = useIDEStore((s) => s.fileStatuses);

  const content = useIDEStore((s) =>
    activeFile ? s.fileContents[activeFile] ?? "" : ""
  );
  const updateFileContent = useIDEStore((s) => s.updateFileContent);

  const editorRef = useRef<any>(null);
  const prevContentLenRef = useRef<number>(0);

  const isLiveWriting = activeFile ? fileStatuses[activeFile]?.isLiveWriting : false;
  const isAIFile = aiStatus === 'generating' && aiCurrentFile === activeFile;

  // ── Auto-scroll to bottom as content grows (live writing effect) ──
  useEffect(() => {
    if (!editorRef.current || !isLiveWriting) return;
    const editor = editorRef.current;
    const model = editor.getModel();
    if (!model) return;

    const newLen = content.length;
    if (newLen > prevContentLenRef.current) {
      // Scroll to end of file
      const lastLine = model.getLineCount();
      editor.revealLine(lastLine, 1); // 1 = smooth scroll
      // Move cursor to the end
      const lastCol = model.getLineMaxColumn(lastLine);
      editor.setPosition({ lineNumber: lastLine, column: lastCol });
    }
    prevContentLenRef.current = newLen;
  }, [content, isLiveWriting]);

  const handleMount: OnMount = (editor) => {
    editorRef.current = editor;
    prevContentLenRef.current = content.length;
  };

  if (!activeFile) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4" style={{ background: '#0d0d0d' }}>
        <div className="flex flex-col items-center gap-3 opacity-40">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="text-gray-600">
            <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
            <polyline points="13 2 13 9 20 9" />
          </svg>
          <span className="text-[14px] text-gray-600">Select a file to edit</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 min-h-0 min-w-0 overflow-hidden relative">
      {/* Live writing overlay */}
      {(isLiveWriting || isAIFile) && (
        <div className="absolute top-2 right-3 z-10 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/25 text-[11px] text-blue-200 backdrop-blur-sm">
          <Sparkles size={11} className="text-blue-400 animate-pulse" />
          <span className="font-medium">AI is writing code...</span>
          <span className="w-1.5 h-3 bg-blue-400 animate-pulse rounded-sm" />
        </div>
      )}

      <Editor
        key={activeFile}
        height="100%"
        theme="vs-dark"
        language={getLanguage(activeFile)}
        value={content}
        onChange={(value) => {
          if (!isLiveWriting) {
            updateFileContent(activeFile, value ?? "");
          }
        }}
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
          readOnly: isLiveWriting,
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
          <div className="flex items-center justify-center h-full gap-2 text-gray-500 text-[13px]">
            <Loader2 size={14} className="animate-spin" />
            Loading editor...
          </div>
        }
      />
    </div>
  );
}
