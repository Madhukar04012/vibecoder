import { useState, useRef, useEffect } from "react";
import { executeCommand } from "@/lib/studio";

const PROJECT_ID = "demo";

export function AtomsTerminalPanel() {
  type OutputLine = { type: "command" | "stdout" | "stderr"; text: string };
  const [output, setOutput] = useState<OutputLine[]>([]);
  const [input, setInput] = useState("");
  const [running, setRunning] = useState(false);
  const outputEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    outputEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [output]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const appendOutput = (text: string, type: OutputLine["type"] = "stdout") => {
    setOutput((prev) => [...prev, { type, text }]);
  };

  const runCommand = async (cmd: string) => {
    if (!cmd.trim()) return;
    setRunning(true);
    appendOutput(`$ ${cmd}`, "command");
    setInput("");

    try {
      const res = await executeCommand(PROJECT_ID, cmd);
      const lines = res.output.split("\n");
      lines.forEach((line) => appendOutput(line, res.success ? "stdout" : "stderr"));
      if (res.exit_code !== 0) {
        appendOutput(`(exit code: ${res.exit_code})`, "stderr");
      }
    } catch (err) {
      appendOutput(String(err), "stderr");
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
      appendOutput("^C", "command");
      setInput("");
      setRunning(false);
    }
  };

  return (
    <div
      className="flex flex-col h-full min-h-0 font-mono text-[13px]"
      style={{
        background: "#0d0d0d",
        color: "#e5e5e5",
        borderTop: "1px solid var(--atoms-sidebar-border)",
      }}
    >
      <div className="flex items-center px-2 py-1 shrink-0" style={{ background: "#1a1a1a", borderBottom: "1px solid #2a2a2a" }}>
        <span className="text-[#9a9a9a] text-xs">Terminal</span>
      </div>
      <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-2 whitespace-pre-wrap break-words">
        {output.length === 0 && (
          <div className="text-[#6b6b6b] text-xs mb-2">
            Type a command and press Enter. Example: ls, npm install, python main.py
          </div>
        )}
        {output.map((line, i) => {
          const color =
            line.type === "command" ? "#4fc3f7" : line.type === "stderr" ? "#ff5252" : "#e5e5e5";
          return (
            <div key={i} style={{ color }} className="leading-relaxed">
              {line.text}
            </div>
          );
        })}
        <div ref={outputEndRef} />
      </div>
      <form onSubmit={handleSubmit} className="flex items-center gap-2 px-2 py-2 shrink-0 border-t border-[#2a2a2a]">
        <span className="text-[#4fc3f7] shrink-0">$</span>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={running}
          placeholder={running ? "Running..." : "Enter command"}
          className="flex-1 bg-transparent outline-none text-[#e5e5e5] placeholder:text-[#6b6b6b] min-w-0"
        />
      </form>
    </div>
  );
}
