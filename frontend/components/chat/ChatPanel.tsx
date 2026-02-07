'use client';

import { useState } from 'react';
import { Send } from 'lucide-react';

import type { AgentRunState, ChatMessageModel, IntegrationStatus } from '@/components/ide/types';
import { ChatMessage } from '@/components/chat/ChatMessage';
import { ResolveButton } from '@/components/chat/ResolveButton';
import { IssueCard } from '@/components/chat/IssueCard';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export type ResolveStrategy = 'local_fallback' | 'connect_atoms_cloud';

export function ChatPanel({
  messages,
  agentState,
  atomsStatus,
  githubStatus,
  isResolving,
  onResolve,
  onSendMessage,
}: {
  messages: ChatMessageModel[];
  agentState: AgentRunState;
  atomsStatus: IntegrationStatus;
  githubStatus: IntegrationStatus;
  isResolving?: boolean;
  onResolve?: (strategy: ResolveStrategy) => void;
  onSendMessage?: (text: string) => void;
}) {
  const [strategy, setStrategy] = useState<ResolveStrategy>('local_fallback');
  const [draft, setDraft] = useState('');

  const isBlocked = agentState === 'blocked';
  const dimHistory = agentState === 'resolved' || agentState === 'idle';
  const lastMessageId = messages.length ? messages[messages.length - 1]?.id : undefined;

  return (
    <div className="flex h-full flex-col">
      {/* Minimal header */}
      <div className="border-b border-white/10 px-3 py-2">
        <p className="text-[11px] font-medium text-slate-400">COMMAND SURFACE</p>
      </div>

      {/* Message log - flat, aggressive fading */}
      <div className="flex-1 overflow-auto px-3">
        <div className="space-y-0">
          {messages.map((m) => {
            const isLatest = lastMessageId ? m.id === lastMessageId : false;
            const quiet = dimHistory && !isLatest;
            return (
              <div key={m.id} className={quiet ? 'opacity-40' : isLatest ? undefined : 'opacity-40'}>
                <ChatMessage message={m} isLatest={isLatest} />
              </div>
            );
          })}
        </div>
      </div>

      {/* Input anchor - visually emphasized */}
      <div className="border-t border-white/10 p-3">
        <div className="space-y-2">
          {isBlocked ? (
            <div className="space-y-2" aria-label="Blocked integrations panel">
              <div className="flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-xs font-medium text-slate-300">Integrations</p>
                  <p className="mt-0.5 text-[11px] text-slate-400">Optional. Local fallback keeps you moving.</p>
                </div>

                <ResolveButton
                  label="Resolve"
                  ariaLabel="Resolve blocked state"
                  isLoading={isResolving}
                  onClick={() => onResolve?.(strategy)}
                />
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/5 px-2 py-2">
                <p className="text-[11px] font-medium text-slate-300">Resolve using:</p>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant={strategy === 'local_fallback' ? 'primary' : 'secondary'}
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => setStrategy('local_fallback')}
                    aria-label="Resolve using local fallback (recommended)"
                    disabled={isResolving}
                  >
                    Local fallback
                  </Button>
                  <Button
                    type="button"
                    variant={strategy === 'connect_atoms_cloud' ? 'primary' : 'secondary'}
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => setStrategy('connect_atoms_cloud')}
                    aria-label="Resolve by connecting Atoms Cloud"
                    disabled={isResolving}
                  >
                    Connect Cloud
                  </Button>
                </div>
              </div>

              <IssueCard
                title="Enable Atoms Cloud"
                description="Unlock hosted agents + remote execution. Optional: local fallback works without setup."
                primaryActionLabel={atomsStatus === 'connected' ? 'Connected' : 'Connect Atoms Cloud'}
                secondaryActionLabel="What this unlocks"
                status={atomsStatus}
                disabled={atomsStatus === 'connected' || atomsStatus === 'connecting'}
              />

              <IssueCard
                title="Enable GitHub integration"
                description="Unlock repo sync, PR creation, and build log streaming. Optional: local workspace works without GitHub."
                primaryActionLabel={githubStatus === 'connected' ? 'Connected' : 'Connect GitHub'}
                secondaryActionLabel="Why optional"
                status={githubStatus}
                disabled={githubStatus === 'connected' || githubStatus === 'connecting'}
              />

              <div className="rounded-xl border border-white/10 bg-white/[0.02] p-2">
                <div className="flex items-center gap-2">
                  <Input
                    aria-label="Command input"
                    placeholder="Choose resolve option to continue…"
                    disabled
                    className="h-11 border-0 bg-white/5"
                  />
                  <Button variant="secondary" size="icon" aria-label="Execute" disabled className="h-11 w-11">
                    <Send className="h-4 w-4" aria-hidden={true} />
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-white/10 bg-white/[0.02] p-2">
              <form
                className="flex items-center gap-2"
                onSubmit={(e) => {
                  e.preventDefault();
                  const text = draft.trim();
                  if (!text) return;
                  onSendMessage?.(text);
                  setDraft('');
                }}
              >
                <Input
                  aria-label="Command input"
                  placeholder="Enter command…"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  className="h-11 border-0 bg-white/5 focus-visible:bg-white/10 focus-visible:ring-1 focus-visible:ring-violet-500/50"
                />
                <Button
                  variant="secondary"
                  size="icon"
                  aria-label="Execute"
                  type="submit"
                  className="h-11 w-11 bg-violet-500/10 hover:bg-violet-500/20"
                >
                  <Send className="h-4 w-4" aria-hidden={true} />
                </Button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
