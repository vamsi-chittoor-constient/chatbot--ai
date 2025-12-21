"""
MCP Server for Restaurant Operations
=====================================
Model Context Protocol server providing direct tool access to all restaurant operations.
Eliminates hallucinations by providing deterministic database-backed tools.
"""

from app.mcp_server.registry import MCPToolRegistry, get_mcp_registry, get_mcp_tools
from app.mcp_server.menu_tools import MENU_TOOLS
from app.mcp_server.cart_tools import CART_TOOLS

__all__ = [
    "MCPToolRegistry",
    "get_mcp_registry",
    "get_mcp_tools",
    "MENU_TOOLS",
    "CART_TOOLS"
]
