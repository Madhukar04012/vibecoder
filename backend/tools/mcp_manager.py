"""
MCP Manager — Phase 2

Model Context Protocol tool router.
Agents emit tool requests, MCP routes them to handlers.

This abstracts all external integrations:
- GitHub API
- Slack API
- Google APIs
- File system operations
- Custom tools

Usage:
    mcp = MCPManager()
    
    # Register a tool
    mcp.register("github.search", github_search_handler)
    
    # Agent emits tool request
    result = await mcp.execute("github.search", {"query": "auth middleware"})
"""

import asyncio
from typing import Dict, Any, Callable, Awaitable, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ToolCategory(Enum):
    """Categories for MCP tools."""
    FILE_SYSTEM = "file_system"
    VERSION_CONTROL = "version_control"
    API_INTEGRATION = "api_integration"
    CODE_ANALYSIS = "code_analysis"
    DEPLOYMENT = "deployment"
    CUSTOM = "custom"


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    category: ToolCategory
    handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    schema: Optional[Dict[str, Any]] = None
    requires_approval: bool = False
    registered_at: datetime = field(default_factory=datetime.now)


@dataclass
class ToolExecutionResult:
    """Result of a tool execution."""
    tool_name: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    requires_approval: bool = False


class MCPManager:
    """
    Model Context Protocol tool manager.
    
    Central router for all agent tool calls.
    Enforces:
    - Tool registration before use
    - Approval gates for dangerous operations
    - Execution logging
    """
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.execution_log: List[ToolExecutionResult] = []
        self._pending_approvals: Dict[str, Dict[str, Any]] = {}
    
    def register(
        self,
        name: str,
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
        description: str = "",
        category: ToolCategory = ToolCategory.CUSTOM,
        schema: Optional[Dict[str, Any]] = None,
        requires_approval: bool = False,
    ) -> None:
        """
        Register a tool.
        
        Args:
            name: Tool name (e.g., "github.search", "file.write")
            handler: Async function to handle the tool call
            description: Human-readable description
            category: Tool category
            schema: JSON schema for payload validation
            requires_approval: Whether user approval is required
        """
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            category=category,
            handler=handler,
            schema=schema,
            requires_approval=requires_approval,
        )
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name
            
        Returns:
            True if tool was unregistered
        """
        if name in self.tools:
            del self.tools[name]
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name."""
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[ToolDefinition]:
        """
        List registered tools.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of tool definitions
        """
        tools = list(self.tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools
    
    async def execute(
        self,
        tool_name: str,
        payload: Dict[str, Any],
        skip_approval: bool = False,
    ) -> ToolExecutionResult:
        """
        Execute a tool.
        
        Args:
            tool_name: Name of the tool to execute
            payload: Tool payload/arguments
            skip_approval: Skip approval gate (for pre-approved operations)
            
        Returns:
            Execution result
        """
        start_time = datetime.now()
        
        # Check if tool exists
        tool = self.tools.get(tool_name)
        if not tool:
            result = ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=f"Unknown MCP tool: {tool_name}",
            )
            self.execution_log.append(result)
            return result
        
        # Check approval requirement
        if tool.requires_approval and not skip_approval:
            approval_id = f"{tool_name}_{datetime.now().timestamp()}"
            self._pending_approvals[approval_id] = {
                "tool_name": tool_name,
                "payload": payload,
            }
            result = ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error="Approval required",
                requires_approval=True,
            )
            self.execution_log.append(result)
            return result
        
        # Execute the tool
        try:
            tool_result = await tool.handler(payload)
            
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = ToolExecutionResult(
                tool_name=tool_name,
                success=True,
                result=tool_result,
                execution_time_ms=elapsed_ms,
            )
            
        except Exception as e:
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                execution_time_ms=elapsed_ms,
            )
        
        self.execution_log.append(result)
        return result
    
    def get_pending_approvals(self) -> Dict[str, Dict[str, Any]]:
        """Get all pending approval requests."""
        return self._pending_approvals.copy()
    
    async def approve_and_execute(self, approval_id: str) -> Optional[ToolExecutionResult]:
        """
        Approve and execute a pending tool call.
        
        Args:
            approval_id: ID of the pending approval
            
        Returns:
            Execution result or None if not found
        """
        pending = self._pending_approvals.pop(approval_id, None)
        if not pending:
            return None
        
        return await self.execute(
            pending["tool_name"],
            pending["payload"],
            skip_approval=True,
        )
    
    def reject_approval(self, approval_id: str) -> bool:
        """
        Reject a pending approval.
        
        Args:
            approval_id: ID of the pending approval
            
        Returns:
            True if rejected
        """
        return self._pending_approvals.pop(approval_id, None) is not None
    
    def get_execution_log(self, limit: int = 100) -> List[ToolExecutionResult]:
        """Get recent execution log."""
        return self.execution_log[-limit:]
    
    def clear_log(self) -> None:
        """Clear execution log."""
        self.execution_log.clear()


# ─── Global Instance ─────────────────────────────────────────────────────────

_mcp: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """Get the global MCP manager instance."""
    global _mcp
    if _mcp is None:
        _mcp = MCPManager()
        _register_builtin_tools(_mcp)
    return _mcp


def _register_builtin_tools(mcp: MCPManager) -> None:
    """Register built-in tools."""
    
    # File read tool
    async def file_read(payload: Dict[str, Any]) -> Dict[str, Any]:
        path = payload.get("path", "")
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"content": content, "success": True}
        except Exception as e:
            return {"content": "", "success": False, "error": str(e)}
    
    mcp.register(
        "file.read",
        file_read,
        description="Read a file from disk",
        category=ToolCategory.FILE_SYSTEM,
    )
    
    # File write tool (requires approval)
    async def file_write(payload: Dict[str, Any]) -> Dict[str, Any]:
        path = payload.get("path", "")
        content = payload.get("content", "")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    mcp.register(
        "file.write",
        file_write,
        description="Write content to a file",
        category=ToolCategory.FILE_SYSTEM,
        requires_approval=True,
    )
    
    # Shell command tool (requires approval)
    async def shell_run(payload: Dict[str, Any]) -> Dict[str, Any]:
        from backend.tools.shell_executor import get_shell_manager
        
        command = payload.get("command", "")
        cwd = payload.get("cwd")
        
        manager = get_shell_manager()
        session_id = manager.create_session(cwd=cwd)
        
        try:
            result = await manager.execute(session_id, command)
            return result
        finally:
            manager.close_session(session_id)
    
    mcp.register(
        "shell.run",
        shell_run,
        description="Run a shell command",
        category=ToolCategory.FILE_SYSTEM,
        requires_approval=True,
    )
