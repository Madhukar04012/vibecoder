/**
 * VibeCober Studio API - MetaGPT-style IDE + AI Team
 * Connects to /studio endpoints for project, chat, apply, run
 */

import { apiFetch } from "./api";

// ============== Types (aligned with backend studio.py) ==============

export interface FileNode {
  name: string;
  path: string;
  type: "file" | "folder";
  children?: FileNode[] | null;
}

export interface ChatMessage {
  agent: string;
  content: string;
  type: "text" | "file_change" | "error" | "system";
  file_path?: string | null;
  diff?: { before?: string; after?: string } | null;
}

export interface ChatResponse {
  messages: ChatMessage[];
  finished: boolean;
}

export interface ApplyResponse {
  success: boolean;
  file_path: string;
  error?: string | null;
}

export interface RunResponse {
  success: boolean;
  output: string;
  exit_code: number;
}

export interface FileContentResponse {
  content: string;
  path: string;
}

export interface DiffResponse {
  before: string;
  after: string;
}

// Phase 2: Planner output — structured intent, no code
export interface Plan {
  summary: string;
  actions: {
    createFiles: string[];
    modifyFiles: string[];
    runCommands: string[];
  };
}

export interface PlanResponse {
  plan: Plan;
}

// Phase 4.2: Diff Agent — minimal placeholder (lib/diff removed)
export interface DiffPlan {
  changes?: Array<{ path: string; content: string }>;
  [key: string]: unknown;
}

export interface DiffPlanRequest {
  plan: Plan;
  files: Record<string, string>;
}

export interface DiffPlanResponse {
  diffPlan: DiffPlan;
}

// MetaGPT-style agent definitions (for UI)
export const AGENTS = [
  { id: "team_lead", name: "Team Lead", profile: "Mike", color: "#4fc3f7", icon: "🧠" },
  { id: "planner", name: "Planner", profile: "Architect", color: "#81c784", icon: "📋" },
  { id: "coder", name: "Coder", profile: "Engineer", color: "#64b5f6", icon: "⚙️" },
  { id: "tester", name: "Tester", profile: "QA", color: "#ffb74d", icon: "🧪" },
  { id: "deployer", name: "Deployer", profile: "DevOps", color: "#ba68c8", icon: "🚀" },
] as const;

export type AgentId = (typeof AGENTS)[number]["id"];

export function getAgentById(id: string) {
  if (id === "user") {
    return { id: "user", name: "User", profile: "You", color: "#4fc3f7", icon: "👤" };
  }
  return AGENTS.find((a) => a.id === id) ?? { ...AGENTS[0], profile: id };
}

// ============== API Functions ==============

export async function getProjectTree(projectId: string): Promise<FileNode[]> {
  return apiFetch<FileNode[]>(`/studio/project/${projectId}`);
}

export async function getPlan(prompt: string): Promise<PlanResponse> {
  return apiFetch<PlanResponse>('/studio/plan', {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  });
}

export async function getDiffPlan(
  plan: Plan,
  files: Record<string, string>
): Promise<DiffPlanResponse> {
  return apiFetch<DiffPlanResponse>('/studio/diff-plan', {
    method: 'POST',
    body: JSON.stringify({
      plan: {
        summary: plan.summary,
        actions: plan.actions,
      },
      files,
    }),
  });
}

export interface EngineerResponse {
  file: string;
  content: string;
}

export async function runEngineer(
  plan: Plan,
  filePath: string
): Promise<EngineerResponse> {
  return apiFetch<EngineerResponse>('/studio/engineer', {
    method: 'POST',
    body: JSON.stringify({
      plan: {
        summary: plan.summary,
        actions: plan.actions,
      },
      file_path: filePath,
    }),
  });
}

export async function getFileContent(
  projectId: string,
  path: string
): Promise<FileContentResponse> {
  return apiFetch<FileContentResponse>(
    `/studio/file?project_id=${encodeURIComponent(projectId)}&path=${encodeURIComponent(path)}`
  );
}

export async function chat(
  projectId: string,
  message: string,
  mode: string = "full"
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/studio/chat", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, message, mode }),
  });
}

export async function applyChange(
  projectId: string,
  filePath: string,
  content: string
): Promise<ApplyResponse> {
  return apiFetch<ApplyResponse>("/studio/apply", {
    method: "POST",
    body: JSON.stringify({
      project_id: projectId,
      file_path: filePath,
      content,
    }),
  });
}

export async function runCommand(
  projectId: string,
  command: "run" | "test" | "build" | "deploy"
): Promise<RunResponse> {
  return apiFetch<RunResponse>("/studio/run", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, command }),
  });
}

export async function executeCommand(
  projectId: string,
  command: string
): Promise<RunResponse> {
  return apiFetch<RunResponse>("/studio/execute", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, command }),
  });
}

export async function getDiff(
  projectId: string,
  path: string
): Promise<DiffResponse> {
  return apiFetch<DiffResponse>(
    `/studio/diff?project_id=${encodeURIComponent(projectId)}&path=${encodeURIComponent(path)}`
  );
}

export interface PreviewStartResponse {
  url: string;
  ready: boolean;
  error?: string | null;
}

export async function startPreview(projectId: string): Promise<PreviewStartResponse> {
  return apiFetch<PreviewStartResponse>('/studio/preview/start', {
    method: 'POST',
    body: JSON.stringify({ project_id: projectId }),
  });
}
