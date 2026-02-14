/**
 * Agent Orchestrator — routes messages, runs agents (Claude), handles delegation and tool use.
 */

import Anthropic from "@anthropic-ai/sdk";
import { AGENTS } from "@/agents/definitions";
import { IDE_TOOLS } from "@/tools";

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
  private client: Anthropic | null = null;
  private state: ProjectState;
  private onMessage: (msg: Message) => void;
  private onStep: () => void;
  private onApprovalRequired: (plan: string, onApprove: () => void) => void;

  constructor(
    onMessage: (msg: Message) => void,
    onStep: () => void = () => {},
    onApprovalRequired: (plan: string, onApprove: () => void) => void = (_p, fn) => fn()
  ) {
    const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY as string | undefined;
    if (apiKey) {
      this.client = new Anthropic({ apiKey });
    }
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

  private buildMessagesForAPI(currentInput: string): Anthropic.MessageParam[] {
    const out: Anthropic.MessageParam[] = [];
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

  private buildToolDefinitions(): Anthropic.Tool[] {
    return IDE_TOOLS.map((tool) => ({
      name: tool.name,
      description: tool.description,
      input_schema: {
        type: "object" as const,
        properties: {
          path: { type: "string" as const, description: "File path" },
          content: { type: "string" as const, description: "File content" },
          command: { type: "string" as const, description: "Shell command" },
        },
      },
    }));
  }

  private async runAgent(agentName: string, input: string): Promise<void> {
    const agent = AGENTS[agentName];
    if (!agent) return;

    if (!this.client) {
      this.onMessage({
        role: "assistant",
        agent: agentName,
        content: "Error: VITE_ANTHROPIC_API_KEY is not set. Add it to your .env to use the agent chat.",
        timestamp: new Date(),
      });
      return;
    }

    const messages = this.buildMessagesForAPI(input);
    const tools = agent.can_use_tools ? this.buildToolDefinitions() : undefined;

    try {
      const response = await this.client.messages.create({
        model: "claude-sonnet-4-20250514",
        max_tokens: 8192,
        system: agent.system_prompt,
        messages,
        tools,
      });

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

  private async processResponse(agentName: string, response: Anthropic.Message): Promise<void> {
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
    previousResponse: Anthropic.Message,
    toolBlock: { type: "tool_use"; id: string; name: string; input: Record<string, unknown> },
    toolResult: unknown
  ): Promise<void> {
    const agent = AGENTS[agentName];
    if (!agent || !this.client) return;

    const userContent: Anthropic.MessageParam["content"] = [
      {
        type: "tool_result",
        tool_use_id: toolBlock.id,
        content: JSON.stringify(toolResult),
      },
    ];

    const response = await this.client.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 8192,
      system: agent.system_prompt,
      messages: [
        ...this.buildMessagesForAPI(""),
        { role: "assistant", content: previousResponse.content },
        { role: "user", content: userContent },
      ],
      tools: this.buildToolDefinitions(),
    });

    await this.processResponse(agentName, response);
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
