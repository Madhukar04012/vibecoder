/**
 * AgentPanel - Shows all AI agents with live status
 * 
 * Displays team members like in the reference design.
 */

import { useAgentStore, type Agent, type AgentState } from '@/stores/agent-store';
import { cn } from '@/lib/utils';
import {
  Crown, ClipboardList, Layers, Code2, ShieldCheck, Rocket,
  Brain, Loader2, CheckCircle2, AlertCircle, Clock, Pause,
  Server, Database, Layout
} from 'lucide-react';

const ICONS: Record<string, typeof Crown> = {
  'crown': Crown,
  'clipboard-list': ClipboardList,
  'layers': Layers,
  'code-2': Code2,
  'shield-check': ShieldCheck,
  'rocket': Rocket,
  'brain': Brain,
  'server': Server,
  'database': Database,
  'layout': Layout,
};

const STATE_CONFIG: Record<AgentState, { icon: typeof Loader2; label: string; animation?: string }> = {
  idle: { icon: Pause, label: 'Idle' },
  thinking: { icon: Brain, label: 'Thinking', animation: 'animate-pulse' },
  working: { icon: Loader2, label: 'Working', animation: 'animate-spin' },
  reviewing: { icon: ShieldCheck, label: 'Reviewing', animation: 'animate-pulse' },
  waiting: { icon: Clock, label: 'Waiting' },
  done: { icon: CheckCircle2, label: 'Done' },
  error: { icon: AlertCircle, label: 'Error' },
};

interface AgentAvatarProps {
  agent: Agent;
  isActive: boolean;
  onClick: () => void;
}

function AgentAvatar({ agent, isActive, onClick }: AgentAvatarProps) {
  const Icon = ICONS[agent.icon] || Brain;
  const stateConfig = STATE_CONFIG[agent.state];
  const StateIcon = stateConfig.icon;
  const isWorking = agent.state === 'working' || agent.state === 'thinking';
  
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'relative flex items-center gap-3 w-full px-3 py-2.5 rounded-lg transition-all',
        'hover:bg-white/5',
        isActive && 'bg-white/10 ring-1 ring-white/20'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'relative w-9 h-9 rounded-lg flex items-center justify-center',
          'transition-all duration-300',
          isWorking && 'ring-2 ring-offset-2 ring-offset-zinc-900'
        )}
        style={{
          backgroundColor: `${agent.color}20`,
          borderColor: agent.color,
        }}
      >
        <Icon size={18} style={{ color: agent.color }} />
        
        {/* Status indicator */}
        <div
          className={cn(
            'absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full flex items-center justify-center',
            'bg-zinc-900 border-2 border-zinc-800'
          )}
        >
          <StateIcon
            size={10}
            className={cn(
              stateConfig.animation,
              agent.state === 'done' && 'text-green-400',
              agent.state === 'error' && 'text-red-400',
              agent.state === 'working' && 'text-blue-400',
              agent.state === 'thinking' && 'text-purple-400',
              agent.state === 'idle' && 'text-zinc-500'
            )}
          />
        </div>
      </div>
      
      {/* Info */}
      <div className="flex-1 text-left min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white truncate">
            {agent.profile}
          </span>
        </div>
        <span className="text-xs text-zinc-500 truncate block">
          {agent.currentTask || stateConfig.label}
        </span>
      </div>
      
      {/* Progress indicator for working state */}
      {isWorking && (
        <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
      )}
    </button>
  );
}

export function AgentPanel() {
  const agents = useAgentStore((s) => s.agents);
  const activeAgent = useAgentStore((s) => s.activeAgent);
  const setActiveAgent = useAgentStore((s) => s.setActiveAgent);
  const roundNumber = useAgentStore((s) => s.roundNumber);
  
  const workingAgents = agents.filter(a => a.state === 'working' || a.state === 'thinking');
  
  return (
    <div className="flex flex-col h-full bg-zinc-900/50">
      {/* Header */}
      <div className="px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white">AI Team</h3>
          {roundNumber > 0 && (
            <span className="text-xs text-zinc-500">Round {roundNumber}</span>
          )}
        </div>
        {workingAgents.length > 0 && (
          <p className="text-xs text-blue-400 mt-1">
            {workingAgents.length} agent{workingAgents.length > 1 ? 's' : ''} working...
          </p>
        )}
      </div>
      
      {/* Agent List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {agents.map((agent) => (
          <AgentAvatar
            key={agent.id}
            agent={agent}
            isActive={activeAgent === agent.name}
            onClick={() => setActiveAgent(agent.name === activeAgent ? null : agent.name)}
          />
        ))}
      </div>
      
      {/* Team Stats */}
      <div className="px-4 py-3 border-t border-zinc-800">
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="text-zinc-500">
            Active: <span className="text-white">{workingAgents.length}/{agents.length}</span>
          </div>
          <div className="text-zinc-500 text-right">
            Status: <span className={cn(
              workingAgents.length > 0 ? 'text-green-400' : 'text-zinc-400'
            )}>
              {workingAgents.length > 0 ? 'Running' : 'Ready'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AgentPanel;
