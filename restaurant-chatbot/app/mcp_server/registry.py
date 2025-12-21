"""
MCP Tool Registry
=================
Central registry for all MCP tools.
Provides a single source of truth for tool discovery and invocation.
"""

from typing import List, Dict, Any
from langchain_core.tools import BaseTool
import structlog

from app.mcp_server.menu_tools import MENU_TOOLS
from app.mcp_server.cart_tools import CART_TOOLS

logger = structlog.get_logger("mcp.registry")


class MCPToolRegistry:
    """Registry for all MCP tools."""

    def __init__(self):
        self._tools = {}
        self._register_all_tools()

    def _register_all_tools(self):
        """Register all available MCP tools."""
        # Register menu tools
        for tool in MENU_TOOLS:
            self._tools[tool.name] = tool
            logger.info("Registered menu tool", tool_name=tool.name)

        # Register cart tools
        for tool in CART_TOOLS:
            self._tools[tool.name] = tool
            logger.info("Registered cart tool", tool_name=tool.name)

        logger.info("MCP Tool Registry initialized", total_tools=len(self._tools))

    def get_tool(self, name: str) -> BaseTool:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Get tools filtered by category."""
        if category == "menu":
            return MENU_TOOLS
        elif category == "cart":
            return CART_TOOLS
        return []

    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return list(self._tools.keys())

    def tool_info(self) -> Dict[str, Any]:
        """Get information about all registered tools."""
        return {
            "total_tools": len(self._tools),
            "categories": {
                "menu": len(MENU_TOOLS),
                "cart": len(CART_TOOLS)
            },
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "args": tool.args if hasattr(tool, 'args') else {}
                }
                for tool in self._tools.values()
            ]
        }


# Global registry instance
_registry = None


def get_mcp_registry() -> MCPToolRegistry:
    """Get the global MCP tool registry instance."""
    global _registry
    if _registry is None:
        _registry = MCPToolRegistry()
    return _registry


def get_mcp_tools() -> List[BaseTool]:
    """Convenience function to get all MCP tools."""
    return get_mcp_registry().get_all_tools()
