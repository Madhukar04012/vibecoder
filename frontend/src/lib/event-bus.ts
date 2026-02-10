/**
 * Atmos Event Bus — Central nervous system of the IDE
 * 
 * ALL communication between panels goes through events.
 * No direct component-to-component calls.
 * 
 * Rule: Every action = event. Every reaction = subscription.
 */

// ─── Event Types ────────────────────────────────────────────────────────────

export type AtmosEventType =
  // File System
  | 'FILE_CREATED'
  | 'FILE_UPDATED'
  | 'FILE_DELETED'
  | 'FILE_RENAMED'
  | 'FILE_OPENED'
  | 'FILE_CLOSED'
  | 'FILE_SAVED'
  // Editor
  | 'EDITOR_CONTENT_CHANGED'
  | 'EDITOR_SELECTION_CHANGED'
  | 'EDITOR_TAB_SWITCHED'
  // AI
  | 'AI_REQUEST'
  | 'AI_THINKING'
  | 'AI_DIFF_READY'
  | 'AI_DIFF_APPLIED'
  | 'AI_DIFF_REJECTED'
  | 'AI_AGENT_START'
  | 'AI_AGENT_END'
  | 'AI_FILE_WRITING'
  | 'AI_FILE_DELTA'
  | 'AI_FILE_COMPLETE'
  | 'AI_MESSAGE'
  | 'AI_MESSAGE_TOKEN'
  | 'AI_ERROR'
  | 'AI_DONE'
  // Execution
  | 'RUN_START'
  | 'RUN_OUTPUT'
  | 'RUN_COMPLETE'
  | 'RUN_ERROR'
  // Preview
  | 'PREVIEW_REFRESH'
  | 'PREVIEW_READY'
  | 'PREVIEW_ERROR'
  // Layout
  | 'PANEL_TOGGLE'
  | 'VIEW_SWITCH'
  // Project
  | 'PROJECT_CREATED'
  | 'PROJECT_RESET'
  // ATMOS (AI-Only)
  | 'ATMOS_PHASE_CHANGE'
  | 'ATMOS_STATUS'
  | 'ATMOS_ERROR_FIXING'
  | 'ATMOS_DONE';

// ─── Event Payloads ─────────────────────────────────────────────────────────

export interface AtmosEvent<T = unknown> {
  type: AtmosEventType;
  payload: T;
  timestamp: number;
  source?: string; // which panel emitted
}

// ─── Typed Payloads ─────────────────────────────────────────────────────────

export interface FilePayload {
  path: string;
  content?: string;
  version?: number;
}

export interface DiffPayload {
  filePath: string;
  before: string;
  after: string;
  agent?: string;
}

export interface AgentPayload {
  agent: string;
  name: string;
  icon: string;
  description?: string;
  result?: string;
}

export interface RunPayload {
  command?: string;
  output?: string;
  exitCode?: number;
  success?: boolean;
}

export interface MessagePayload {
  content: string;
  token?: string;
  role?: 'user' | 'assistant' | 'system';
}

// ─── Event Bus Implementation ───────────────────────────────────────────────

type Listener = (event: AtmosEvent) => void;

class EventBusImpl {
  private listeners: Map<AtmosEventType, Set<Listener>> = new Map();
  private globalListeners: Set<Listener> = new Set();
  private history: AtmosEvent[] = [];
  private maxHistory = 200;

  /** Subscribe to a specific event type */
  on(type: AtmosEventType, listener: Listener): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)!.add(listener);
    return () => this.listeners.get(type)?.delete(listener);
  }

  /** Subscribe to ALL events (for debugging / logging) */
  onAll(listener: Listener): () => void {
    this.globalListeners.add(listener);
    return () => this.globalListeners.delete(listener);
  }

  /** Emit an event to all subscribers */
  emit<T = unknown>(type: AtmosEventType, payload: T, source?: string): void {
    const event: AtmosEvent<T> = {
      type,
      payload,
      timestamp: Date.now(),
      source,
    };

    // Record history
    this.history.push(event as AtmosEvent);
    if (this.history.length > this.maxHistory) {
      this.history = this.history.slice(-this.maxHistory);
    }

    // Notify type-specific listeners
    const typeListeners = this.listeners.get(type);
    if (typeListeners) {
      typeListeners.forEach((l) => {
        try { l(event as AtmosEvent); } catch (e) { console.error(`[EventBus] Error in ${type} listener:`, e); }
      });
    }

    // Notify global listeners
    this.globalListeners.forEach((l) => {
      try { l(event as AtmosEvent); } catch (e) { console.error(`[EventBus] Error in global listener:`, e); }
    });
  }

  /** Get event history (for debugging) */
  getHistory(): AtmosEvent[] {
    return [...this.history];
  }

  /** Clear all listeners */
  clear(): void {
    this.listeners.clear();
    this.globalListeners.clear();
    this.history = [];
  }
}

// ─── Singleton ──────────────────────────────────────────────────────────────

export const EventBus = new EventBusImpl();

// ─── React Hook ─────────────────────────────────────────────────────────────

import { useEffect, useRef, useCallback } from 'react';

/** Hook to subscribe to events in React components */
export function useEventBus(type: AtmosEventType, handler: (event: AtmosEvent) => void): void {
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  useEffect(() => {
    return EventBus.on(type, (event) => handlerRef.current(event));
  }, [type]);
}

/** Hook to emit events */
export function useEmit() {
  return useCallback(<T = unknown>(type: AtmosEventType, payload: T, source?: string) => {
    EventBus.emit(type, payload, source);
  }, []);
}
