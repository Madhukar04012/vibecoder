import { useState } from "react";
import { Plus, Users, User, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";

export function AtomsChatPanel({ embedded }: { embedded?: boolean }) {
  const [teamMode, setTeamMode] = useState(true); // team = active, single = inactive

  return (
    <aside
      className={cn(
        "flex flex-col h-full",
        embedded ? "w-full min-w-0" : "shrink-0"
      )}
      style={
        embedded
          ? { background: "var(--atoms-sidebar-bg)" }
          : {
              width: "42%",
              minWidth: 360,
              maxWidth: 520,
              background: "var(--atoms-sidebar-bg)",
              borderRight: "1px solid var(--atoms-sidebar-border)",
            }
      }
    >
      {/* Header */}
      {embedded && (
        <div className="shrink-0 px-3 py-2 flex items-center gap-2 text-[13px] text-[#9a9a9a] border-b border-[#252525]">
          <MessageSquare size={14} className="text-[#6b6b6b]" />
          <span>Chat</span>
        </div>
      )}
      {/* CHAT HISTORY - empty, clean */}
      <div className="flex-1 overflow-y-auto min-h-0" />

      {/* CHAT INPUT - matches image: tall container, placeholder top, buttons bottom */}
      <div className="px-3 py-3 shrink-0">
        <div
          className="flex flex-col rounded-lg overflow-hidden w-full min-h-[100px] transition-all duration-300 focus-within:ring-1 focus-within:ring-[#404040] focus-within:ring-offset-1 focus-within:ring-offset-transparent border border-[#333]"
          style={{ background: "#252525" }}
        >
          <textarea
            rows={3}
            className="flex-1 bg-transparent outline-none text-[13px] text-[#e5e5e5] placeholder:text-[#7a7a7a] min-w-0 resize-none px-4 pt-4 pb-2 leading-relaxed transition-colors duration-200 focus:placeholder:text-[#5a5a5a]"
            placeholder="Ask the team to bring your idea to life"
          />
          <div className="flex items-center justify-between px-3 pb-3 pt-1">
            <div className="flex items-center gap-1">
              <button
                className="w-9 h-9 rounded-md flex items-center justify-center text-white bg-[#2c2c2c] hover:bg-[#3a3a3a] hover:scale-105 active:scale-95 transition-all duration-200"
                aria-label="Add"
              >
                <Plus size={18} />
              </button>
              <button
                onClick={() => setTeamMode(true)}
                className={cn(
                  "w-9 h-9 rounded-md flex items-center justify-center text-white transition-all duration-200",
                  teamMode ? "bg-[#3c3c3c] scale-105" : "bg-[#2c2c2c] hover:bg-[#3a3a3a] hover:scale-105 active:scale-95"
                )}
                aria-label="Team"
              >
                <Users size={18} />
              </button>
              <button
                onClick={() => setTeamMode(false)}
                className={cn(
                  "w-9 h-9 rounded-md flex items-center justify-center text-white transition-all duration-200",
                  !teamMode ? "bg-[#3c3c3c] scale-105" : "bg-[#2c2c2c] hover:bg-[#3a3a3a] hover:scale-105 active:scale-95"
                )}
                aria-label="Single user"
              >
                <User size={18} />
              </button>
            </div>
            <button
              className="w-9 h-9 rounded-xl flex items-center justify-center text-white bg-[#3c3c3c] hover:bg-[#4a4a4a] hover:scale-105 active:scale-95 transition-all duration-200"
              aria-label="Send"
            >
              <span className="text-lg leading-none">↑</span>
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
