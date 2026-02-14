"""MCP Server entry point with Streamable HTTP transport."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn

from .config import settings
from .db import database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
mcp_server = Server("rpg-mcp")

# Tool registry - populated by register_tools()
_all_tools: list[Tool] = []
_tool_handlers: dict[str, callable] = {}

# Streamable HTTP session manager - stateless, JSON-only responses
session_manager = StreamableHTTPSessionManager(
    app=mcp_server,
    stateless=True,
    json_response=True,
)


def register_tools():
    """Register all MCP tools by collecting from all modules."""
    from .tools import world_creation
    from .tools import characters
    from .tools import items
    from .tools import quests
    from .tools import groups
    from .tools import queries
    from .tools import dice_tools
    from .tools import encounters
    
    # Collect tools and handlers from all modules
    # Note: time_tools removed - game time is tracked via events, not separate state
    modules = [
        world_creation,
        characters,
        items,
        quests,
        groups,
        queries,
        dice_tools,
        encounters,
    ]
    
    for module in modules:
        tools, handlers = module.get_tools()
        _all_tools.extend(tools)
        _tool_handlers.update(handlers)
    
    logger.info(f"Registered {len(_all_tools)} tools")


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return _all_tools


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Route tool calls to the appropriate handler."""
    handler = _tool_handlers.get(name)
    if handler:
        return await handler(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


@asynccontextmanager
async def lifespan(app: Starlette):
    """Application lifespan manager."""
    # Startup
    logger.info("Connecting to MongoDB...")
    await database.connect()
    logger.info("MongoDB connected")
    
    # Register tools
    register_tools()
    
    # Initialize session manager
    async with session_manager.run():
        yield
    
    # Shutdown
    logger.info("Disconnecting from MongoDB...")
    await database.disconnect()
    logger.info("MongoDB disconnected")


async def health_check(request):
    """Health check endpoint."""
    return JSONResponse({"status": "healthy", "service": "rpg-mcp"})


# Create Starlette app
# Note: Starlette's Mount causes 307 redirects for paths without trailing slash
# MCP spec doesn't mandate a specific path, so we use /mcp/ (with slash) 
# and ensure clients use the trailing slash to avoid redirects
app = Starlette(
    debug=True,
    lifespan=lifespan,
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Mount("/mcp", app=session_manager.handle_request),
    ]
)


def main():
    """Run the MCP server."""
    logger.info(f"Starting RPG MCP server on {settings.host}:{settings.port}")
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
