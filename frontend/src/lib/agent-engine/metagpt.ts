/**
 * MetaGPT Agent Adapter - Atmos Mode
 * 
 * Wraps MetaGPT as a reasoning engine.
 * MetaGPT does NOT control execution.
 * MetaGPT outputs ONLY file changes.
 * 
 * Rules:
 * - Single run, no rounds
 * - Output normalized to AgentChange[]
 * - Bad output = empty array
 */

import type { AgentEngine, AgentChange, WorkspaceContext } from "./types";
import { getApiUrl } from "@/lib/api";

export class MetaGPTAgent implements AgentEngine {
    private apiEndpoint = getApiUrl("/api/agent/metagpt");

    async generateChanges({
        prompt,
        context,
        files,
    }: {
        prompt: string;
        context: WorkspaceContext;
        files: Record<string, string>;
    }): Promise<AgentChange[]> {
        // 1. Build deterministic input with strict header
        const input = this.buildInput(prompt, context, files);

        // 2. Call MetaGPT backend (single run, no rounds)
        const rawOutput = await this.runMetaGPT(input);

        // 3. Normalize output → file changes only
        return this.normalize(rawOutput);
    }

    private buildInput(
        prompt: string,
        context: WorkspaceContext,
        files: Record<string, string>
    ): { systemPrompt: string; userPrompt: string; files: Record<string, string> } {
        const systemPrompt = `You are modifying an existing codebase.

Rules:
- Output ONLY JSON.
- JSON must be an array of { path, content }.
- Do NOT explain.
- Do NOT include markdown.
- Do NOT include roles, plans, or messages.

Workspace context:
Active files: ${context.active.join(", ") || "none"}
Recently opened: ${context.opened.slice(0, 5).join(", ") || "none"}
Recently modified: ${context.modified.slice(0, 5).join(", ") || "none"}`;

        return {
            systemPrompt,
            userPrompt: `User request:\n${prompt}`,
            files,
        };
    }

    private async runMetaGPT(input: {
        systemPrompt: string;
        userPrompt: string;
        files: Record<string, string>;
    }): Promise<unknown> {
        try {
            const res = await fetch(this.apiEndpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(input),
            });

            if (!res.ok) {
                console.error("[MetaGPT] API error:", res.status);
                return null;
            }

            return await res.json();
        } catch (err) {
            console.error("[MetaGPT] Network error:", err);
            return null;
        }
    }

    private normalize(output: unknown): AgentChange[] {
        // Safety gate: only accept arrays of { path, content }
        if (!Array.isArray(output)) {
            console.warn("[MetaGPT] Output not an array, discarding");
            return [];
        }

        return output.filter(
            (c): c is AgentChange =>
                typeof c?.path === "string" &&
                typeof c?.content === "string" &&
                c.path.length > 0
        );
    }
}

// Factory function for easy swapping
export function createMetaGPTEngine(): AgentEngine {
    return new MetaGPTAgent();
}
