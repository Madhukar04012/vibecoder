import { useIDEStore } from "@/stores/ide-store";
import { useNavigate } from "react-router-dom";
import { useState, useCallback, useRef, useEffect } from "react";
import { SettingsPanel } from './SettingsPanel';
import { Settings, Home, PlusCircle, FolderOpen, Sparkles, X, Search, Filter, Crown, Database, Code2, Layers, Shield } from 'lucide-react';

const AGENT_FILTERS = [
  { value: null, label: 'All', icon: null },
  { value: 'Team Leader', label: 'Team Lead', icon: Crown },
  { value: 'Database Engineer', label: 'Database', icon: Database },
  { value: 'Backend Engineer', label: 'Backend', icon: Code2 },
  { value: 'Frontend Engineer', label: 'Frontend', icon: Layers },
  { value: 'QA Engineer', label: 'QA', icon: Shield },
] as const;

export function ChatTopBar() {
  const clearChat = useIDEStore((s) => s.clearChat);
  const chatMessages = useIDEStore((s) => s.chatMessages);
  const aiStatus = useIDEStore((s) => s.aiStatus);
  const chatSearchQuery = useIDEStore((s) => s.chatSearchQuery);
  const setChatSearchQuery = useIDEStore((s) => s.setChatSearchQuery);
  const chatAgentFilter = useIDEStore((s) => s.chatAgentFilter);
  const setChatAgentFilter = useIDEStore((s) => s.setChatAgentFilter);
  const navigate = useNavigate();
  const [showSettings, setShowSettings] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [showFilter, setShowFilter] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const filterRef = useRef<HTMLDivElement>(null);

  const handleNewChat = () => {
    clearChat();
    setChatSearchQuery('');
    setChatAgentFilter(null);
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

  const toggleSearch = useCallback(() => {
    setShowSearch(prev => {
      if (prev) {
        setChatSearchQuery('');
      }
      return !prev;
    });
  }, [setChatSearchQuery]);

  // Focus search input when opened
  useEffect(() => {
    if (showSearch && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [showSearch]);

  // Keyboard shortcut: Ctrl+F to toggle search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        toggleSearch();
      }
      if (e.key === 'Escape' && showSearch) {
        setShowSearch(false);
        setChatSearchQuery('');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showSearch, toggleSearch, setChatSearchQuery]);

  // Close filter dropdown on outside click
  useEffect(() => {
    if (!showFilter) return;
    const handleClick = (e: MouseEvent) => {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setShowFilter(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [showFilter]);

  // Count matching messages for search
  const matchCount = chatSearchQuery.trim()
    ? chatMessages.filter(m => m.content.toLowerCase().includes(chatSearchQuery.toLowerCase())).length
    : 0;

  const isActive = aiStatus === 'thinking' || aiStatus === 'generating' || aiStatus === 'streaming';

  return (
    <div className="relative shrink-0">
      {/* Header Bar */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{
          borderBottom: showSearch ? 'none' : '1px solid var(--ide-border)',
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
          {/* Search button */}
          <button
            onClick={toggleSearch}
            className="p-2 rounded-lg transition-all hover:bg-zinc-700/50"
            style={{ color: showSearch ? 'var(--accent, #818cf8)' : 'var(--ide-text-muted)' }}
            title="Search messages (Ctrl+F)"
          >
            <Search size={16} />
          </button>
          {/* Filter button */}
          <div ref={filterRef} className="relative">
            <button
              onClick={() => setShowFilter(f => !f)}
              className="p-2 rounded-lg transition-all hover:bg-zinc-700/50"
              style={{ color: chatAgentFilter ? 'var(--accent, #818cf8)' : 'var(--ide-text-muted)' }}
              title="Filter by agent"
            >
              <Filter size={16} />
            </button>
            {/* Filter dropdown */}
            {showFilter && (
              <div
                className="absolute right-0 top-full mt-1 z-50 rounded-lg border shadow-xl"
                style={{
                  background: 'var(--ide-surface)',
                  borderColor: 'var(--ide-border)',
                  minWidth: 160,
                }}
              >
                {AGENT_FILTERS.map(({ value, label, icon: Icon }) => (
                  <button
                    key={label}
                    type="button"
                    onClick={() => {
                      setChatAgentFilter(value);
                      setShowFilter(false);
                    }}
                    className="flex items-center gap-2 w-full px-3 py-2 text-left text-[12px] transition-colors hover:bg-zinc-700/50"
                    style={{
                      color: chatAgentFilter === value ? 'var(--accent, #818cf8)' : 'var(--ide-text)',
                      fontFamily: 'var(--font-ui)',
                      fontWeight: chatAgentFilter === value ? 600 : 400,
                    }}
                  >
                    {Icon && <Icon size={13} className="shrink-0 opacity-60" />}
                    {!Icon && <span className="w-[13px]" />}
                    {label}
                    {chatAgentFilter === value && (
                      <span className="ml-auto text-[10px] opacity-60">&#10003;</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
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

      {/* Search Bar — slides down below header */}
      {showSearch && (
        <div
          className="flex items-center gap-2 px-4 py-2"
          style={{
            borderBottom: '1px solid var(--ide-border)',
            background: 'var(--ide-surface)',
          }}
        >
          <Search size={14} style={{ color: 'var(--ide-text-muted)', flexShrink: 0 }} />
          <input
            ref={searchInputRef}
            type="text"
            value={chatSearchQuery}
            onChange={(e) => setChatSearchQuery(e.target.value)}
            placeholder="Search messages..."
            className="flex-1 bg-transparent border-none outline-none text-[13px]"
            style={{
              color: 'var(--ide-text)',
              fontFamily: 'var(--font-ui)',
              caretColor: 'var(--accent, #818cf8)',
            }}
          />
          {chatSearchQuery && (
            <span className="text-[11px] shrink-0" style={{ color: 'var(--ide-text-muted)', fontFamily: 'var(--font-mono)' }}>
              {matchCount} match{matchCount !== 1 ? 'es' : ''}
            </span>
          )}
          <button
            type="button"
            onClick={() => { setShowSearch(false); setChatSearchQuery(''); }}
            className="p-1 rounded hover:bg-zinc-700/50"
            style={{ color: 'var(--ide-text-muted)', lineHeight: 0 }}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Active filter indicator */}
      {chatAgentFilter && (
        <div
          className="flex items-center gap-2 px-4 py-1.5"
          style={{
            borderBottom: '1px solid var(--ide-border)',
            background: 'rgba(99,102,241,0.06)',
          }}
        >
          <Filter size={11} style={{ color: 'var(--accent, #818cf8)' }} />
          <span className="text-[11px] font-medium" style={{ color: 'var(--accent, #818cf8)', fontFamily: 'var(--font-ui)' }}>
            Showing: {chatAgentFilter}
          </span>
          <button
            type="button"
            onClick={() => setChatAgentFilter(null)}
            className="ml-auto p-0.5 rounded hover:bg-zinc-700/50"
            style={{ color: 'var(--ide-text-muted)', lineHeight: 0 }}
            title="Clear filter"
          >
            <X size={12} />
          </button>
        </div>
      )}

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
