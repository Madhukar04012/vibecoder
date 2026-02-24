/**
 * NovaIDE - Professional AI-Powered IDE
 * 
 * Layout: Chat (left) + Explorer + Editor (center) + Preview
 * Clean, modern design with smooth transitions.
 */

import { useEffect, useState } from 'react';
import { Group, Panel, Separator } from 'react-resizable-panels';
import { cn } from '@/lib/utils';
import { AtomsChatPanel } from '@/components/AtomsChatPanel';
import { AgentChat } from '@/components/AgentChat';
import FilePanel from '@/components/layout/FilePanel';
import { EditorPanel } from '@/components/editor/EditorPanel';
import { Code2, Eye, Globe } from 'lucide-react';

import { restoreIDEState, useIDEStore } from '@/stores/ide-store';
import { useAtmosStore } from '@/lib/atmos-state';
import { useEventBus } from '@/lib/event-bus';
import { installIdeAPI, uninstallIdeAPI } from '@/lib/ide-bridge';

type ViewMode = 'editor' | 'viewer';
type ChatMode = 'atoms' | 'agents';

export default function NovaIDE() {
  const [viewMode, setViewMode] = useState<ViewMode>('editor');
  const [chatMode, setChatMode] = useState<ChatMode>('agents');
  const previewUrl = useAtmosStore((s) => s.previewUrl);
  const phase = useAtmosStore((s) => s.phase);

  // Restore state on boot
  useEffect(() => {
    restoreIDEState();
  }, []);

  // Wire IDE bridge so agent tools can read/write files and use terminal
  useEffect(() => {
    installIdeAPI(useIDEStore.getState);
    return () => uninstallIdeAPI();
  }, []);

  // Auto-View Switching based on phase
  useEventBus('ATMOS_PHASE_CHANGE', (event) => {
    const { phase: newPhase } = event.payload as { phase: string };
    if (newPhase === 'live') setViewMode('viewer');
    if (newPhase === 'generating') setViewMode('editor');
  });

  const isLive = phase === 'live';

  return (
    <div className="h-screen w-screen overflow-hidden" style={{ background: 'var(--ide-bg)', color: 'var(--ide-text)' }}>
      <div className="h-full w-full flex flex-col overflow-hidden">
        {/* Main Content */}
        <div className="flex-1 flex min-h-0 min-w-0 overflow-hidden relative">

          <Group orientation="horizontal" id="atmos-main-v3">
            {/* Chat Panel */}
            <Panel id="atmos-chat" defaultSize={35} minSize={"320px"}>
              <div className="h-full flex flex-col overflow-hidden relative" style={{ background: 'var(--ide-chat-bg)', borderRight: '1px solid var(--ide-border)', zIndex: 100 }}>
                <div className="shrink-0 flex p-1 gap-1 rounded-lg" style={{ background: 'var(--ide-bg)', margin: 8 }}>
                  <button
                    type="button"
                    onClick={() => setChatMode('atoms')}
                    className={cn('flex-1 px-3 py-1.5 text-[12px] rounded-md transition-colors', chatMode === 'atoms' ? 'font-medium' : '')}
                    style={{ background: chatMode === 'atoms' ? 'var(--ide-surface-hover)' : 'transparent', color: chatMode === 'atoms' ? 'var(--ide-text)' : 'var(--ide-text-muted)' }}
                  >
                    Atoms
                  </button>
                  <button
                    type="button"
                    onClick={() => setChatMode('agents')}
                    className={cn('flex-1 px-3 py-1.5 text-[12px] rounded-md transition-colors', chatMode === 'agents' ? 'font-medium' : '')}
                    style={{ background: chatMode === 'agents' ? 'var(--ide-surface-hover)' : 'transparent', color: chatMode === 'agents' ? 'var(--ide-text)' : 'var(--ide-text-muted)' }}
                  >
                    Agents
                  </button>
                </div>
                <div className="flex-1 min-h-0 overflow-hidden">
                  {chatMode === 'atoms' && <AtomsChatPanel embedded />}
                  {chatMode === 'agents' && <AgentChat />}
                </div>
              </div>
            </Panel>

            {/* Drag Handle */}
            <Separator className="w-[5px] bg-transparent hover:bg-gradient-to-b hover:from-blue-500/30 hover:via-purple-500/30 hover:to-blue-500/30 active:bg-blue-500/50 transition-all duration-200 cursor-col-resize" />

            {/* Editor + Preview */}
            <Panel id="atmos-editor" defaultSize={65} minSize={"200px"}>
              <div className="h-full w-full flex flex-col min-h-0 min-w-0 overflow-hidden" style={{ background: 'var(--ide-bg-deep)' }}>
                {/* View Mode Tabs */}
                <div
                  className="shrink-0 flex items-center justify-between px-4 py-2"
                  style={{ background: 'var(--ide-surface)', borderBottom: '1px solid var(--ide-border)' }}
                >
                  {/* Tab Switcher */}
                  <div className="flex items-center p-1 rounded-xl" style={{ background: 'var(--ide-bg)' }}>
                    <button
                      onClick={() => setViewMode('editor')}
                      className={cn(
                        'flex items-center gap-2 px-4 py-2 text-[13px] rounded-lg transition-all duration-200',
                        viewMode === 'editor'
                          ? 'font-medium shadow-sm'
                          : 'hover:bg-zinc-700/30'
                      )}
                      style={{
                        background: viewMode === 'editor' ? 'var(--ide-surface-hover)' : 'transparent',
                        color: viewMode === 'editor' ? 'var(--ide-text)' : 'var(--ide-text-muted)',
                      }}
                    >
                      <Code2 size={15} className={viewMode === 'editor' ? 'text-blue-400' : ''} />
                      <span>Code</span>
                    </button>
                    <button
                      onClick={() => setViewMode('viewer')}
                      className={cn(
                        'flex items-center gap-2 px-4 py-2 text-[13px] rounded-lg transition-all duration-200',
                        viewMode === 'viewer'
                          ? 'font-medium shadow-sm'
                          : 'hover:bg-zinc-700/30'
                      )}
                      style={{
                        background: viewMode === 'viewer' ? 'var(--ide-surface-hover)' : 'transparent',
                        color: viewMode === 'viewer' ? 'var(--ide-text)' : 'var(--ide-text-muted)',
                      }}
                    >
                      <Eye size={15} className={viewMode === 'viewer' ? 'text-green-400' : ''} />
                      <span>Preview</span>
                      {isLive && (
                        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                      )}
                    </button>
                  </div>

                  {/* Status Badge */}
                  {previewUrl && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px]" style={{ background: 'var(--ide-bg)', color: 'var(--ide-text-muted)' }}>
                      <Globe size={14} className="text-green-400" />
                      <span>{new URL(previewUrl).host}</span>
                    </div>
                  )}
                </div>

                {/* Editor View */}
                <div className={cn('flex-1 flex min-h-0 min-w-0 overflow-hidden', viewMode !== 'editor' && 'hidden')}>
                  <div className="flex h-full min-h-0 min-w-0 overflow-hidden w-full">
                    <div className="w-60 min-w-[200px] max-w-[300px] shrink-0" style={{ background: 'var(--ide-panel-bg)', borderRight: '1px solid var(--ide-border)' }}>
                      <FilePanel />
                    </div>
                    <div className="flex-1 min-w-0 h-full">
                      <EditorPanel />
                    </div>
                  </div>
                </div>

                {/* Preview View */}
                <div className={cn('flex-1 min-h-0 min-w-0 overflow-hidden', viewMode !== 'viewer' && 'hidden')}>
                  {previewUrl ? (
                    <iframe
                      src={previewUrl}
                      title="Preview"
                      className="h-full w-full border-0"
                      style={{ background: '#ffffff' }}
                    />
                  ) : (
                    <div className="h-full w-full flex flex-col items-center justify-center gap-4" style={{ background: 'var(--ide-bg-deep)' }}>
                      <div className="w-20 h-20 rounded-2xl flex items-center justify-center" style={{ background: 'var(--ide-surface)' }}>
                        <Globe size={36} style={{ color: 'var(--ide-text-muted)' }} />
                      </div>
                      <div className="text-center">
                        <p className="text-[15px] font-medium mb-1" style={{ color: 'var(--ide-text)' }}>No preview available</p>
                        <p className="text-[13px]" style={{ color: 'var(--ide-text-muted)' }}>Preview will appear when the app is running</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </Panel>
          </Group>
        </div>
      </div>
    </div>
  );
}
