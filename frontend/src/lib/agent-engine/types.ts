/**
 * Agent Engine Contract - Atmos Mode
 * 
 * The IDE only talks to this interface.
 * Engines produce file changes, nothing else.
 */

export interface WorkspaceContext {
    active: string[];
    opened: string[];
    modified: string[];
}

export interface AgentChange {
    path: string;
    content: string;
}

export interface AgentEngine {
    generateChanges(input: {
        prompt: string;
        context: WorkspaceContext;
        files: Record<string, string>;
    }): Promise<AgentChange[]>;
}
