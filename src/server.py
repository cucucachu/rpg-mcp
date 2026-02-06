"""MCP Server entry point with SSE transport."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, Response
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

# SSE transport - shared across requests
sse_transport = SseServerTransport("/messages/")


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
    
    yield
    
    # Shutdown
    logger.info("Disconnecting from MongoDB...")
    await database.disconnect()
    logger.info("MongoDB disconnected")


async def health_check(request):
    """Health check endpoint."""
    return JSONResponse({"status": "healthy", "service": "rpg-mcp"})


async def handle_sse(request):
    """Handle SSE connections for MCP."""
    async with sse_transport.connect_sse(
        request.scope,
        request.receive,
        request._send
    ) as streams:
        await mcp_server.run(
            streams[0],
            streams[1],
            mcp_server.create_initialization_options()
        )
    # Return empty response to avoid NoneType error when client disconnects
    return Response()


# Create Starlette app
app = Starlette(
    debug=True,
    lifespan=lifespan,
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Route("/sse", handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse_transport.handle_post_message),
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
