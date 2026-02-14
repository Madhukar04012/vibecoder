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

// Default agents matching the backend roles
const DEFAULT_AGENTS: Agent[] = [
  {
    id: '1',
    name: 'team_leader',
    profile: 'Team Leader',
    goal: 'Coordinate the team',
    icon: 'crown',
    color: '#f59e0b',
    state: 'idle',
  },
  {
    id: '2',
    name: 'product_manager',
    profile: 'Product Manager',
    goal: 'Define requirements',
    icon: 'clipboard-list',
    color: '#8b5cf6',
    state: 'idle',
  },
  {
    id: '3',
    name: 'architect',
    profile: 'Architect',
    goal: 'Design the system',
    icon: 'layers',
    color: '#06b6d4',
    state: 'idle',
  },
  {
    id: '4',
    name: 'engineer',
    profile: 'Engineer',
    goal: 'Write code',
    icon: 'code-2',
    color: '#22c55e',
    state: 'idle',
  },
  {
    id: '5',
    name: 'qa_engineer',
    profile: 'QA Engineer',
    goal: 'Test and review',
    icon: 'shield-check',
    color: '#f97316',
    state: 'idle',
  },
  {
    id: '6',
    name: 'devops',
    profile: 'DevOps',
    goal: 'Deploy and monitor',
    icon: 'rocket',
    color: '#ef4444',
    state: 'idle',
  },
];

export const useAgentStore = create<AgentStore>((set, get) => ({
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
