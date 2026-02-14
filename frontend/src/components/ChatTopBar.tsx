import { useIDEStore } from "@/stores/ide-store";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { SettingsPanel } from './SettingsPanel';
import { Settings, Home, PlusCircle, FolderOpen, Sparkles, X } from 'lucide-react';

export function ChatTopBar() {
  const clearChat = useIDEStore((s) => s.clearChat);
  const chatMessages = useIDEStore((s) => s.chatMessages);
  const aiStatus = useIDEStore((s) => s.aiStatus);
  const navigate = useNavigate();
  const [showSettings, setShowSettings] = useState(false);

  const handleNewChat = () => {
    clearChat();
  };

  const handleHome = () => {
    navigate('/dashboard');
  };

  const handleProject = () => {
    navigate("/dashboard");
  };

  const handleSettings = () => {
    setShowSettings(true);
  };

  const isActive = aiStatus === 'thinking' || aiStatus === 'generating' || aiStatus === 'streaming';

  return (
    <div className="relative shrink-0">
      {/* Header Bar */}
      <div 
        className="flex items-center justify-between px-4 py-3"
        style={{ 
          borderBottom: '1px solid var(--ide-border)',
          background: 'var(--ide-surface)'
        }}
      >
        {/* Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <h1 className="text-[14px] font-semibold" style={{ color: 'var(--ide-text)' }}>Videcoder</h1>
            <p className="text-[10px]" style={{ color: 'var(--ide-text-muted)' }}>
              {isActive ? (
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                  AI is working...
                </span>
              ) : chatMessages.length > 0 ? (
                `${chatMessages.length} messages`
              ) : (
                'Ready to build'
              )}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={handleNewChat}
            className="p-2 rounded-lg transition-all hover:bg-zinc-700/50"
            style={{ color: 'var(--ide-text-muted)' }}
            title="New chat"
          >
            <PlusCircle size={18} />
          </button>
          <button
            onClick={handleHome}
            className="p-2 rounded-lg transition-all hover:bg-zinc-700/50"
            style={{ color: 'var(--ide-text-muted)' }}
            title="Dashboard"
          >
            <Home size={18} />
          </button>
          <button
            onClick={handleProject}
            className="p-2 rounded-lg transition-all hover:bg-zinc-700/50"
            style={{ color: 'var(--ide-text-muted)' }}
            title="Projects"
          >
            <FolderOpen size={18} />
          </button>
          <button
            onClick={handleSettings}
            className="p-2 rounded-lg transition-all hover:bg-zinc-700/50"
            style={{ color: 'var(--ide-text-muted)' }}
            title="Settings"
          >
            <Settings size={18} />
          </button>
        </div>
      </div>

      {/* Settings Panel Overlay */}
      {showSettings && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center" style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)' }}>
          <div className="w-[95vw] h-[95vh] max-w-7xl rounded-xl overflow-hidden shadow-2xl border" style={{ background: 'var(--ide-bg)', borderColor: 'var(--ide-border)' }}>
            <div className="h-full relative">
              <SettingsPanel />
              <button
                onClick={() => setShowSettings(false)}
                className="absolute top-4 right-4 z-[10000] p-2 rounded-lg hover:bg-zinc-700 transition-colors"
                style={{
                  background: 'var(--ide-surface)',
                  color: 'var(--ide-text)',
                  border: '1px solid var(--ide-border)'
                }}
              >
                <X size={18} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
