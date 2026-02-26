/**
 * Agent Store - Zustand state for multi-agent team
 * 
 * Tracks all AI agents, their states, and activities.
 */

import { create } from 'zustand';

export type AgentState = 'idle' | 'thinking' | 'working' | 'reviewing' | 'waiting' | 'done' | 'error';

export interface Agent {
  id: string;
  name: string;
  profile: string;
  goal: string;
  icon: string;
  color: string;
  state: AgentState;
  currentTask?: string;
  progress?: number;
  lastActivity?: string;
  tokenUsage?: number;
  cost?: number;
  model?: string;   // NIM model name (e.g., "Nemotron 49B")
}

export interface AgentMessage {
  id: string;
  from: string;
  fromProfile: string;
  to?: string;
  content: string;
  timestamp: Date;
  type: 'discussion' | 'status' | 'artifact' | 'error';
  icon?: string;
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'backlog' | 'in_progress' | 'review' | 'done';
  assignee?: string;
  priority: 'low' | 'medium' | 'high';
  createdAt: Date;
}

interface AgentStore {
  // Agents
  agents: Agent[];
  activeAgent: string | null;
  
  // Messages/Discussion
  messages: AgentMessage[];
  
  // Tasks
  tasks: Task[];
  
  // Metrics
  totalCost: number;
  totalTokens: number;
  roundNumber: number;
  
  // Actions
  setAgents: (agents: Agent[]) => void;
  updateAgent: (name: string, updates: Partial<Agent>) => void;
  setActiveAgent: (name: string | null) => void;
  addMessage: (message: Omit<AgentMessage, 'id' | 'timestamp'>) => void;
  addTask: (task: Omit<Task, 'id' | 'createdAt'>) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  updateMetrics: (cost: number, tokens: number) => void;
  setRound: (round: number) => void;
  reset: () => void;
}

// Default agents — IDs and names match NIM streaming roles exactly
// so updateAgent(event.agent, ...) works directly from nim-ws.ts
const DEFAULT_AGENTS: Agent[] = [
  {
    id: 'team_lead',
    name: 'team_lead',
    profile: 'Team Leader',
    goal: 'Plan work and coordinate the team',
    icon: 'crown',
    color: '#f59e0b',
    state: 'idle',
    model: 'Nemotron 49B',
  },
  {
    id: 'database_engineer',
    name: 'database_engineer',
    profile: 'Database Engineer',
    goal: 'Design schema and data models',
    icon: 'database',
    color: '#3b82f6',
    state: 'idle',
    model: 'Llama 3.3 70B',
  },
  {
    id: 'backend_engineer',
    name: 'backend_engineer',
    profile: 'Backend Engineer',
    goal: 'Build API and business logic',
    icon: 'server',
    color: '#22c55e',
    state: 'idle',
    model: 'Devstral 123B',
  },
  {
    id: 'frontend_engineer',
    name: 'frontend_engineer',
    profile: 'Frontend Engineer',
    goal: 'Build UI and user experience',
    icon: 'layout',
    color: '#06b6d4',
    state: 'idle',
    model: 'Qwen 2.5 Coder 32B',
  },
  {
    id: 'qa_engineer',
    name: 'qa_engineer',
    profile: 'QA Engineer',
    goal: 'Validate and ensure quality',
    icon: 'shield-check',
    color: '#f97316',
    state: 'idle',
    model: 'QWQ 32B',
  },
];

export const useAgentStore = create<AgentStore>((set) => ({
  agents: DEFAULT_AGENTS,
  activeAgent: null,
  messages: [],
  tasks: [],
  totalCost: 0,
  totalTokens: 0,
  roundNumber: 0,
  
  setAgents: (agents) => set({ agents }),
  
  updateAgent: (name, updates) => set((state) => ({
    agents: state.agents.map((a) =>
      a.name === name ? { ...a, ...updates } : a
    ),
  })),
  
  setActiveAgent: (name) => set({ activeAgent: name }),
  
  addMessage: (message) => set((state) => ({
    messages: [
      ...state.messages,
      {
        ...message,
        id: Math.random().toString(36).substr(2, 9),
        timestamp: new Date(),
      },
    ],
  })),
  
  addTask: (task) => set((state) => ({
    tasks: [
      ...state.tasks,
      {
        ...task,
        id: Math.random().toString(36).substr(2, 9),
        createdAt: new Date(),
      },
    ],
  })),
  
  updateTask: (id, updates) => set((state) => ({
    tasks: state.tasks.map((t) =>
      t.id === id ? { ...t, ...updates } : t
    ),
  })),
  
  updateMetrics: (cost, tokens) => set((state) => ({
    totalCost: state.totalCost + cost,
    totalTokens: state.totalTokens + tokens,
  })),
  
  setRound: (round) => set({ roundNumber: round }),
  
  reset: () => set({
    agents: DEFAULT_AGENTS,
    activeAgent: null,
    messages: [],
    tasks: [],
    totalCost: 0,
    totalTokens: 0,
    roundNumber: 0,
  }),
}));
