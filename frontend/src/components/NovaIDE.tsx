/**
 * NovaIDE - AI-Powered IDE Layout
 * Cursor/Replit-style: Chat + File Explorer + Editor + Terminal
 */

import { useState, useCallback, useEffect } from 'react';
import { Group, Panel, Separator } from 'react-resizable-panels';
import { cn } from '@/lib/utils';
import { AtomsTopBar } from '@/components/AtomsTopBar';
import { AtomsChatPanel } from '@/components/AtomsChatPanel';
import FilePanel from '@/components/layout/FilePanel';
import { EditorPanel } from '@/components/editor/EditorPanel';
import { AtomsTerminalPanel } from '@/components/AtomsTerminalPanel';
import { AtomsAgentTimelineOverlay } from '@/components/AtomsAgentTimelineOverlay';
import { useIDEStore, restoreIDEState } from '@/stores/ide-store';
import { executeCommand, startPreview } from '@/lib/studio';
import { EventBus, useEventBus } from '@/lib/event-bus';

type ViewMode = 'editor' | 'viewer' | 'terminal';

export default function NovaIDE() {
  const PROJECT_ID = 'demo';
  const { workspaceMode, project, addActivity } = useIDEStore();

  const [viewMode, setViewMode] = useState<ViewMode>('editor');
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isSplit, setIsSplit] = useState(false);
  const [showTimeline, setShowTimeline] = useState(false);
  const [showTerminal, setShowTerminal] = useState(false);

  // Restore state on boot
  useEffect(() => {
    restoreIDEState();
  }, []);

  // Auto-switch to preview when AI finishes deploying
  useEventBus('PREVIEW_READY', (event) => {
    const url = (event.payload as { url: string }).url;
    setPreviewUrl(url);
    setViewMode('viewer');
    setShowTerminal(false);
  });

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey;
      if (mod && e.key === 'b') {
        e.preventDefault();
        setSidebarVisible((v) => !v);
        return;
      }
      if (mod && e.key === '`') {
        e.preventDefault();
        setShowTerminal((v) => !v);
        return;
      }
      if (mod && e.key === 'Enter') {
        e.preventDefault();
        setViewMode((m) => (m === 'editor' ? 'viewer' : 'editor'));
        return;
      }
      if (mod && e.key === '\\') {
        e.preventDefault();
        setIsSplit((s) => !s);
        return;
      }
      if (mod && e.shiftKey && e.key.toLowerCase() === 'l') {
        e.preventDefault();
        setShowTimeline((v) => !v);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // Preview
  useEffect(() => {
    if (viewMode === 'viewer' && workspaceMode === 'project') {
      startPreview(PROJECT_ID)
        .then((r) => setPreviewUrl(r.url))
        .catch(() => setPreviewUrl('http://127.0.0.1:5174'));
    } else {
      setPreviewUrl(null);
    }
  }, [viewMode, workspaceMode]);

  // Build command
  const handlePublish = useCallback(async () => {
    if (workspaceMode !== 'project') return;
    setShowTerminal(true);
    try {
      const res = await executeCommand(PROJECT_ID, 'npm run build');
      addActivity(res.success ? 'Build completed' : 'Build failed', res.output, res.success);
    } catch (e) {
      addActivity('Build failed', (e as Error)?.message, false);
    }
  }, [workspaceMode, addActivity]);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden" style={{ background: '#0a0a0a', color: '#e5e5e5' }}>
      {/* Top Bar */}
      <AtomsTopBar
        view={viewMode === 'viewer' ? 'app' : viewMode === 'terminal' ? 'terminal' : 'editor'}
        setView={(v) => {
          if (v === 'terminal') setShowTerminal((t) => !t);
          else setViewMode(v === 'app' ? 'viewer' : v === 'terminal' ? 'terminal' : 'editor');
        }}
        sidebarVisible={sidebarVisible}
        onToggleSidebar={() => setSidebarVisible((v) => !v)}
        onPublish={handlePublish}
        projectName={project?.name ?? 'New Project'}
      />

      {/* Main Content */}
      <div className="flex-1 flex min-h-0 min-w-0 overflow-hidden">
        <Group orientation="horizontal" className="flex-1">
          {/* Chat Panel */}
          {sidebarVisible && (
            <>
              <Panel defaultSize="30" minSize="20" maxSize="45">
                <div className="h-full border-r border-[#1a1a1a]">
                  <AtomsChatPanel embedded />
                </div>
              </Panel>
              <Separator className="w-[3px] hover:bg-blue-500/30 transition-colors" />
            </>
          )}

          {/* File Explorer */}
          {sidebarVisible && (
            <>
              <Panel defaultSize="15" minSize="10" maxSize="25">
                <div className="h-full border-r border-[#1a1a1a]">
                  <FilePanel />
                </div>
              </Panel>
              <Separator className="w-[3px] hover:bg-blue-500/30 transition-colors" />
            </>
          )}

          {/* Editor + Terminal */}
          <Panel defaultSize="55" minSize="30">
            <Group orientation="vertical">
              {/* Editor / Preview */}
              <Panel defaultSize={showTerminal ? "70" : "100"} minSize="30">
                <div className="h-full w-full flex flex-col min-h-0 min-w-0 overflow-hidden" style={{ background: '#0d0d0d' }}>
                  {/* Editor View */}
                  <div className={cn('flex-1 flex flex-col min-h-0 min-w-0 overflow-hidden', viewMode !== 'editor' && 'hidden')}>
                    <EditorPanel isSplit={isSplit} />
                  </div>

                  {/* Preview View */}
                  <div className={cn('flex-1 min-h-0 min-w-0 overflow-hidden', viewMode !== 'viewer' && 'hidden')}>
                    <iframe
                      src={previewUrl || 'about:blank'}
                      title="Preview"
                      className="h-full w-full border-0"
                      style={{ background: '#1e1e1e' }}
                    />
                  </div>
                </div>
              </Panel>

              {/* Terminal */}
              {showTerminal && (
                <>
                  <Separator className="h-[3px] hover:bg-blue-500/30 transition-colors" />
                  <Panel defaultSize="30" minSize="15" maxSize="50">
                    <AtomsTerminalPanel />
                  </Panel>
                </>
              )}
            </Group>
          </Panel>
        </Group>
      </div>

      {/* Agent Timeline Overlay */}
      {showTimeline && (
        <AtomsAgentTimelineOverlay onClose={() => setShowTimeline(false)} />
      )}
    </div>
  );
}
