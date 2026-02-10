/**
 * NovaIDE - ATMOS AI-Only Layout
 * 
 * ATMOS Core Law: User expresses intent. AI decides everything else.
 * 
 * Layout: Chat (left, resizable) + Explorer + Editor (center) + Preview
 * ALL views are ATMOS-controlled. No manual triggers.
 * No terminal panel. No keyboard shortcuts. No manual execution.
 */

import { useEffect, useState } from 'react';
import { Group, Panel, Separator } from 'react-resizable-panels';
import { cn } from '@/lib/utils';
import { AtomsChatPanel } from '@/components/AtomsChatPanel';
import FilePanel from '@/components/layout/FilePanel';
import { EditorPanel } from '@/components/editor/EditorPanel';
import { useIDEStore, restoreIDEState } from '@/stores/ide-store';
import { useAtmosStore } from '@/lib/atmos-state';
import { useEventBus } from '@/lib/event-bus';

type ViewMode = 'editor' | 'viewer';

export default function NovaIDE() {
  const [viewMode, setViewMode] = useState<ViewMode>('editor');
  const previewUrl = useAtmosStore((s) => s.previewUrl);
  const project = useIDEStore((s) => s.project);

  // Restore state on boot
  useEffect(() => {
    restoreIDEState();
  }, []);

  // ── ATMOS Auto-View Switching ──────────────────────────────────────────────
  useEventBus('ATMOS_PHASE_CHANGE', (event) => {
    const { phase: newPhase } = event.payload as { phase: string };
    if (newPhase === 'live') setViewMode('viewer');
    if (newPhase === 'generating') setViewMode('editor');
  });

  // ── ATMOS File Events → IDE Store ──────────────────────────────────────────
  useEventBus('FILE_CREATED', (event) => {
    const { path, content } = event.payload as { path: string; content: string };
    const store = useIDEStore.getState();
    store.createFile(path, content || '');
    if (store.openFiles.length === 0) store.openFile(path);
  });

  useEventBus('FILE_UPDATED', (event) => {
    const { path, content } = event.payload as { path: string; content: string };
    useIDEStore.getState().createFile(path, content || '');
  });

  return (
    <div className="h-screen w-screen overflow-hidden" style={{ background: '#0a0a0a', color: '#e5e5e5' }}>
      <div className="h-full w-full flex flex-col overflow-hidden">
        {/* Main Content — resizable chat + editor (NO TOP BAR) */}
        <div className="flex-1 flex min-h-0 min-w-0 overflow-hidden relative">
          
          <Group orientation="horizontal" id="atmos-main-v3">
            {/* Chat Panel — resizable with pixel-based min */}
            <Panel id="atmos-chat" defaultSize={35} minSize={"320px"}>
              <div className="h-full border-r border-[#1a1a1a] overflow-hidden" style={{ background: '#111111' }}>
                <AtomsChatPanel embedded />
              </div>
            </Panel>

            {/* Drag Handle */}
            <Separator className="w-[4px] bg-transparent hover:bg-blue-500/40 active:bg-blue-500/60 transition-colors cursor-col-resize" />

            {/* Editor + Preview — fills remaining space */}
            <Panel id="atmos-editor" defaultSize={65} minSize={"200px"}>
              <div className="h-full w-full flex flex-col min-h-0 min-w-0 overflow-hidden" style={{ background: '#0d0d0d' }}>
                {/* Tabs: Code / Preview */}
                <div className="shrink-0 flex items-center gap-1 px-3 py-2 border-b border-[#1a1a1a]" style={{ background: '#0a0a0a' }}>
                  <button
                    onClick={() => setViewMode('editor')}
                    className={cn(
                      'px-3 py-1.5 text-[12px] rounded-md transition-all',
                      viewMode === 'editor'
                        ? 'bg-[#1a1a1a] text-white font-medium'
                        : 'text-gray-500 hover:text-gray-300 hover:bg-[#141414]'
                    )}
                  >
                    <span className="opacity-60 mr-1.5">&lt;/&gt;</span> Code
                  </button>
                  <button
                    onClick={() => setViewMode('viewer')}
                    className={cn(
                      'px-3 py-1.5 text-[12px] rounded-md transition-all',
                      viewMode === 'viewer'
                        ? 'bg-[#1a1a1a] text-white font-medium'
                        : 'text-gray-500 hover:text-gray-300 hover:bg-[#141414]'
                    )}
                  >
                    <span className="opacity-60 mr-1.5">◎</span> Preview
                  </button>
                </div>

                {/* Editor View */}
                <div className={cn('flex-1 flex min-h-0 min-w-0 overflow-hidden', viewMode !== 'editor' && 'hidden')}>
                  <div className="flex h-full min-h-0 min-w-0 overflow-hidden w-full">
                    <div className="w-56 min-w-[180px] max-w-[280px] border-r border-[#1a1a1a] bg-[#0b0b0b] shrink-0">
                      <FilePanel />
                    </div>
                    <div className="flex-1 min-w-0">
                      <EditorPanel />
                    </div>
                  </div>
                </div>

                {/* Preview View — auto-activated when ATMOS reaches LIVE */}
                <div className={cn('flex-1 min-h-0 min-w-0 overflow-hidden', viewMode !== 'viewer' && 'hidden')}>
                  {previewUrl ? (
                    <iframe
                      src={previewUrl}
                      title="Preview"
                      className="h-full w-full border-0"
                      style={{ background: '#1e1e1e' }}
                    />
                  ) : (
                    <div className="h-full w-full flex items-center justify-center text-gray-600 text-[13px]">
                      Preview will appear when the app is running
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
