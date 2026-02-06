"""MCP server for RPG utilities - runs locally via stdio."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .dice import roll_dice, roll_multiple, random_choice, coin_flip, percentile, DiceResult


# Create MCP server
server = Server("rpg-utilities")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available utility tools."""
    return [
        Tool(
            name="roll_dice",
            description="Roll dice using standard notation (e.g., '2d6+3', '1d20', '4d6kh3' for keep highest 3, '2d20adv' for advantage)",
            inputSchema={
                "type": "object",
                "properties": {
                    "notation": {
                        "type": "string",
                        "description": "Dice notation (e.g., '2d6+3', '1d20', '4d6kh3', '2d20adv')"
                    },
                    "times": {
                        "type": "integer",
                        "description": "Number of times to roll (default 1)",
                        "default": 1
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for the roll (for logging)"
                    }
                },
                "required": ["notation"]
            }
        ),
        Tool(
            name="random_table",
            description="Pick randomly from a list of options, optionally with weights",
            inputSchema={
                "type": "object",
                "properties": {
                    "options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of options to choose from"
                    },
                    "weights": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Optional weights for each option (higher = more likely)"
                    },
                    "table_name": {
                        "type": "string",
                        "description": "Optional name for the table (for logging)"
                    }
                },
                "required": ["options"]
            }
        ),
        Tool(
            name="coin_flip",
            description="Flip a coin - returns 'heads' or 'tails'",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="percentile",
            description="Roll a percentile die (1-100)",
            inputSchema={
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for the roll"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="roll_stats",
            description="Roll a standard set of ability scores (4d6 drop lowest, 6 times)",
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "Rolling method: '4d6kh3' (default), '3d6', '2d6+6'",
                        "default": "4d6kh3"
                    }
                },
                "required": []
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "roll_dice":
        notation = arguments["notation"]
        times = arguments.get("times", 1)
        reason = arguments.get("reason", "")
        
        try:
            if times == 1:
                result = roll_dice(notation)
                output = {
                    "notation": result.notation,
                    "rolls": result.rolls,
                    "modifier": result.modifier,
                    "total": result.total,
                    "details": result.details
                }
                if result.dropped:
                    output["dropped"] = result.dropped
                if reason:
                    output["reason"] = reason
            else:
                results = roll_multiple(notation, times)
                output = {
                    "notation": notation,
                    "times": times,
                    "results": [
                        {
                            "rolls": r.rolls,
                            "total": r.total,
                            "dropped": r.dropped
                        }
                        for r in results
                    ],
                    "totals": [r.total for r in results],
                    "sum": sum(r.total for r in results)
                }
                if reason:
                    output["reason"] = reason
            
            return [TextContent(type="text", text=json.dumps(output))]
        
        except ValueError as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
    
    elif name == "random_table":
        options = arguments["options"]
        weights = arguments.get("weights")
        table_name = arguments.get("table_name", "")
        
        try:
            index, chosen = random_choice(options, weights)
            output = {
                "chosen": chosen,
                "index": index,
                "from_options": len(options)
            }
            if table_name:
                output["table"] = table_name
            
            return [TextContent(type="text", text=json.dumps(output))]
        
        except ValueError as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
    
    elif name == "coin_flip":
        result = coin_flip()
        return [TextContent(type="text", text=json.dumps({"result": result}))]
    
    elif name == "percentile":
        result = percentile()
        reason = arguments.get("reason", "")
        output = {"roll": result}
        if reason:
            output["reason"] = reason
        return [TextContent(type="text", text=json.dumps(output))]
    
    elif name == "roll_stats":
        method = arguments.get("method", "4d6kh3")
        
        results = roll_multiple(method, 6)
        stats = [r.total for r in results]
        
        output = {
            "method": method,
            "stats": stats,
            "rolls": [
                {
                    "kept": r.rolls,
                    "dropped": r.dropped,
                    "total": r.total
                }
                for r in results
            ],
            "total": sum(stats),
            "suggestion": "Assign these values to your attributes as desired"
        }
        
        return [TextContent(type="text", text=json.dumps(output))]
    
    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def run_server():
    """Run the MCP server via stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
