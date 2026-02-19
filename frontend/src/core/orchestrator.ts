/**
 * Agent Orchestrator — routes messages, runs agents (Claude), handles delegation and tool use.
 * Uses backend proxy for secure API access.
 */

import { AGENTS } from "@/agents/definitions";
import { IDE_TOOLS } from "@/tools";
import { getApiUrl } from "@/lib/api";
import { getStoredToken } from "@/lib/auth-storage";

export interface Message {
  role: "user" | "assistant";
  agent: string;
  content: string;
  timestamp: Date;
}

export interface Task {
  id: string;
  description: string;
  assigned_to: string;
  status: "pending" | "in_progress" | "complete" | "failed";
}

export interface ProjectState {
  messages: Message[];
  tasks: Task[];
  current_agent: string;
  token_usage: number;
}

type ContentBlock = { type: "text"; text: string } | { type: "tool_use"; id: string; name: string; input: Record<string, unknown> };

export class AgentOrchestrator {
  private state: ProjectState;
  private onMessage: (msg: Message) => void;
  private onStep: () => void;
  private onApprovalRequired: (plan: string, onApprove: () => void) => void;
  private toolCallCount: number = 0;
  private readonly MAX_TOOL_CALLS = 10;

  constructor(
    onMessage: (msg: Message) => void,
    onStep: () => void = () => {},
    onApprovalRequired: (plan: string, onApprove: () => void) => void = (_p, fn) => fn()
  ) {
    this.state = {
      messages: [],
      tasks: [],
      current_agent: "mike",
      token_usage: 0,
    };
    this.onMessage = onMessage;
    this.onStep = onStep;
    this.onApprovalRequired = onApprovalRequired;
  }

  async handleUserMessage(userInput: string): Promise<void> {
    this.state.messages.push({
      role: "user",
      agent: "user",
      content: userInput,
      timestamp: new Date(),
    });

    const startAgent = this.routeMessage(userInput);
    await this.runAgent(startAgent, userInput);
  }

  private routeMessage(input: string): string {
    const lowerInput = input.toLowerCase();
    if (lowerInput.includes("@alex")) return "alex";
    if (lowerInput.includes("@iris")) return "iris";
    if (lowerInput.includes("@emma")) return "emma";
    if (lowerInput.includes("@sarah")) return "sarah";
    return "mike";
  }

  private buildMessagesForAPI(currentInput: string): Array<{ role: string; content: string | any[] }> {
    const out: Array<{ role: string; content: string | any[] }> = [];
    for (const msg of this.state.messages) {
      const content = msg.role === "user" ? msg.content : `[${msg.agent.toUpperCase()}]: ${msg.content}`;
      out.push({
        role: msg.role,
        content,
      });
    }
    if (currentInput && this.state.messages[this.state.messages.length - 1]?.role !== "user") {
      out.push({ role: "user", content: currentInput });
    }
    return out;
  }

  private async callBackendChat(
    agentName: string,
    messages: Array<{ role: string; content: string | any[] }>,
    systemPrompt: string,
    canUseTools: boolean
  ): Promise<{ content: any[]; usage?: { input_tokens: number; output_tokens: number } }> {
    const token = getStoredToken();
    const response = await fetch(getApiUrl("api/agent-chat/chat"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        agent_name: agentName,
        messages,
        system_prompt: systemPrompt,
        can_use_tools: canUseTools,
        max_tokens: 8192,
      }),
      signal: AbortSignal.timeout(30000), // 30 second timeout
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  }

  private async runAgent(agentName: string, input: string): Promise<void> {
    const agent = AGENTS[agentName];
    if (!agent) return;

    const messages = this.buildMessagesForAPI(input);

    // Reset tool call counter for new agent run
    this.toolCallCount = 0;

    try {
      const response = await this.callBackendChat(
        agentName,
        messages,
        agent.system_prompt,
        agent.can_use_tools
      );

      const usage = response.usage;
      if (usage) {
        this.state.token_usage += usage.input_tokens + usage.output_tokens;
      }

      await this.processResponse(agentName, response);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      this.onMessage({
        role: "assistant",
        agent: agentName,
        content: `Error: ${message}`,
        timestamp: new Date(),
      });
    }
  }

  private async processResponse(agentName: string, response: { content: any[] }): Promise<void> {
    const content = response.content as ContentBlock[];
    let fullText = "";

    for (const block of content) {
      if (block.type === "text") {
        fullText += block.text;
        const delegation = this.parseDelegation(block.text);
        if (delegation) {
          this.addAgentMessage(agentName, fullText);
          if (delegation.agent === "alex") {
            this.onApprovalRequired(delegation.brief, () =>
              this.runAgent(delegation.agent, delegation.brief)
            );
          } else {
            await this.runAgent(delegation.agent, delegation.brief);
          }
          return;
        }
      }

      if (block.type === "tool_use") {
        // Check tool call limit
        this.toolCallCount++;
        if (this.toolCallCount > this.MAX_TOOL_CALLS) {
          this.addAgentMessage(
            agentName,
            `[System] Tool call limit reached (${this.MAX_TOOL_CALLS} calls). Stopping to prevent infinite loops.`
          );
          return;
        }

        const result = await this.executeTool(block.name, block.input);
        await this.continueAgentWithToolResult(agentName, response, block, result);
        return;
      }
    }

    if (fullText) {
      this.addAgentMessage(agentName, fullText);
    }
  }

  private parseDelegation(text: string): { agent: string; brief: string } | null {
    const match =
      text.match(/DELEGATE_TO:(\w+)\n([\s\S]+)/i) || text.match(/@\s*(\w+)\s+([\s\S]+)/i);
    if (match) {
      return {
        agent: match[1].toLowerCase(),
        brief: match[2].trim(),
      };
    }
    return null;
  }

  private async executeTool(toolName: string, params: Record<string, unknown>): Promise<unknown> {
    this.onStep();
    const tool = IDE_TOOLS.find((t) => t.name === toolName);
    if (!tool) return { error: "Tool not found" };
    return await tool.execute(params);
  }

  private async continueAgentWithToolResult(
    agentName: string,
    previousResponse: { content: any[] },
    toolBlock: { type: "tool_use"; id: string; name: string; input: Record<string, unknown> },
    toolResult: unknown
  ): Promise<void> {
    const agent = AGENTS[agentName];
    if (!agent) return;

    const userContent = [
      {
        type: "tool_result",
        tool_use_id: toolBlock.id,
        content: JSON.stringify(toolResult),
      },
    ];

    const messages = [
      ...this.buildMessagesForAPI(""),
      { role: "assistant", content: previousResponse.content },
      { role: "user", content: userContent },
    ];

    try {
      const response = await this.callBackendChat(
        agentName,
        messages,
        agent.system_prompt,
        true // Tools enabled for continuation
      );

      await this.processResponse(agentName, response);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      this.onMessage({
        role: "assistant",
        agent: agentName,
        content: `Error continuing with tool result: ${message}`,
        timestamp: new Date(),
      });
    }
  }

  private addAgentMessage(agentName: string, content: string): void {
    const msg: Message = {
      role: "assistant",
      agent: agentName,
      content,
      timestamp: new Date(),
    };
    this.state.messages.push(msg);
    this.onMessage(msg);
  }
}
