/**
 * Workspace Context - Atmos Mode
 * Builds context payload from store for agent prompts
 * No UI, no branching, just facts
 */

import { useIDEStore } from "@/stores/ide-store";

export interface WorkspaceContext {
    active: string[];
    opened: string[];
    modified: string[];
}

export function buildWorkspaceContext(): WorkspaceContext {
    const s = useIDEStore.getState();
    return {
        active: s.activeContextFiles,
        opened: s.recentlyOpenedFiles,
        modified: s.recentlyModifiedFiles,
    };
}

export function formatContextForPrompt(ctx: WorkspaceContext): string {
    const lines: string[] = [];

    if (ctx.active.length > 0) {
        lines.push(`Active files: ${ctx.active.join(", ")}`);
    }
    if (ctx.opened.length > 0) {
        lines.push(`Recently opened: ${ctx.opened.slice(0, 5).join(", ")}`);
    }
    if (ctx.modified.length > 0) {
        lines.push(`Recently modified: ${ctx.modified.slice(0, 5).join(", ")}`);
    }

    if (lines.length === 0) return "";
    return `Workspace context:\n${lines.join("\n")}\n\n`;
}
