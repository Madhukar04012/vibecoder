/**
 * AtomsTerminalPanel - Terminal with command execution
 */

import { useState, useRef, useEffect } from "react";
import { Terminal, Trash2 } from "lucide-react";
import { useIDEStore } from "@/stores/ide-store";
import { getApiUrl } from "@/lib/api";

export function AtomsTerminalPanel() {
  const { terminalLines, appendTerminalLine, clearTerminal } = useIDEStore();
  const [input, setInput] = useState("");
  const [running, setRunning] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState(-1);
  const outputEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    outputEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [terminalLines]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const runCommand = async (cmd: string) => {
    if (!cmd.trim()) return;
    setRunning(true);
    setHistory((h) => [...h, cmd]);
    setHistoryIdx(-1);
    appendTerminalLine(`$ ${cmd}`, "command");
    setInput("");

    try {
      const res = await fetch(getApiUrl("/api/run"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cmd }),
      });
      const data = await res.json() as { stdout: string; stderr: string; exitCode: number };

      if (data.stdout) {
        data.stdout.split("\n").forEach((line: string) => appendTerminalLine(line, "stdout"));
      }
      if (data.stderr) {
        data.stderr.split("\n").forEach((line: string) => appendTerminalLine(line, "stderr"));
      }
      if (data.exitCode !== 0) {
        appendTerminalLine(`Process exited with code ${data.exitCode}`, "stderr");
      }
    } catch (err) {
      appendTerminalLine(`Error: ${String(err)}`, "stderr");
    } finally {
      setRunning(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runCommand(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "c" && e.ctrlKey) {
      e.preventDefault();
      appendTerminalLine("^C", "command");
      setInput("");
      setRunning(false);
    }
    if (e.key === "l" && e.ctrlKey) {
      e.preventDefault();
      clearTerminal();
    }
    if (e.key === "ArrowUp" && history.length > 0) {
      e.preventDefault();
      const idx = historyIdx === -1 ? history.length - 1 : Math.max(0, historyIdx - 1);
      setHistoryIdx(idx);
      setInput(history[idx]);
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (historyIdx === -1) return;
      const idx = historyIdx + 1;
      if (idx >= history.length) {
        setHistoryIdx(-1);
        setInput("");
      } else {
        setHistoryIdx(idx);
        setInput(history[idx]);
      }
    }
  };

  return (
    <div
      className="flex flex-col h-full min-h-0 font-mono text-[12px]"
      style={{ background: "#0a0a0a", color: "#e5e5e5" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-1.5 shrink-0 border-b border-[#1a1a1a]" style={{ background: "#111" }}>
        <div className="flex items-center gap-2 text-gray-400">
          <Terminal size={12} />
          <span className="text-[11px] font-medium">Terminal</span>
        </div>
        <button
          onClick={clearTerminal}
          className="p-1 rounded hover:bg-[#2a2a2a] text-gray-600 hover:text-gray-400 transition-colors"
          title="Clear"
        >
          <Trash2 size={12} />
        </button>
      </div>

      {/* Output */}
      <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-3 whitespace-pre-wrap break-words">
        {terminalLines.length === 0 && (
          <div className="text-gray-600 text-[11px] mb-2">
            $ Type a command and press Enter
          </div>
        )}
        {terminalLines.map((line, i) => {
          const color =
            line.type === "command" ? "#60a5fa" : line.type === "stderr" ? "#f87171" : "#d4d4d4";
          return (
            <div key={i} style={{ color }} className="leading-[1.6]">
              {line.text}
            </div>
          );
        })}
        <div ref={outputEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2 px-3 py-2 shrink-0 border-t border-[#1a1a1a]"
        style={{ background: "#0f0f0f" }}
      >
        <span className="text-blue-400 shrink-0 text-[11px]">$</span>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={running}
          placeholder={running ? "Running..." : "Enter command..."}
          className="flex-1 bg-transparent outline-none text-gray-200 placeholder:text-gray-600 min-w-0 text-[12px]"
        />
      </form>
    </div>
  );
}
