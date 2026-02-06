"""Dice tools: roll_dice, roll_table, coin_flip, roll_stat_array."""

import json
from typing import Any
from mcp.types import Tool, TextContent

from ..dice import roll_dice as _roll_dice, roll_multiple, random_choice, coin_flip as _coin_flip, percentile


def get_tools() -> tuple[list[Tool], dict[str, callable]]:
    """Return tools and handlers for dice rolling."""
    tools = [
        Tool(
            name="roll_dice",
            description="Roll dice using standard notation. Supports: '2d6+3', '1d20', '4d6kh3' (keep highest 3), '2d20adv' (advantage), '2d20dis' (disadvantage)",
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
                        "description": "Optional reason for the roll (for logging/display)"
                    }
                },
                "required": ["notation"]
            }
        ),
        Tool(
            name="roll_table",
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
                        "description": "Optional name for the table (for display)"
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
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for the flip"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="roll_stat_array",
            description="Generate ability scores using specified method. Default is 4d6 drop lowest, 6 times.",
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
        Tool(
            name="percentile_roll",
            description="Roll a percentile die (1-100). Useful for random encounters, loot tables, etc.",
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
    ]
    
    handlers = {
        "roll_dice": _handle_roll_dice,
        "roll_table": _handle_roll_table,
        "coin_flip": _handle_coin_flip,
        "roll_stat_array": _handle_roll_stat_array,
        "percentile_roll": _handle_percentile_roll,
    }
    
    return tools, handlers


async def _handle_roll_dice(args: dict[str, Any]) -> list[TextContent]:
    """Handle dice roll requests."""
    notation = args["notation"]
    times = args.get("times", 1)
    reason = args.get("reason", "")
    
    try:
        if times == 1:
            result = _roll_dice(notation)
            output = {
                "notation": result.notation,
                "rolls": result.rolls,
                "modifier": result.modifier,
                "total": result.total,
                "details": result.details,
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
                        "dropped": r.dropped,
                    }
                    for r in results
                ],
                "totals": [r.total for r in results],
                "sum": sum(r.total for r in results),
            }
            if reason:
                output["reason"] = reason
        
        return [TextContent(type="text", text=json.dumps(output))]
    
    except ValueError as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _handle_roll_table(args: dict[str, Any]) -> list[TextContent]:
    """Handle random table picks."""
    options = args["options"]
    weights = args.get("weights")
    table_name = args.get("table_name", "")
    
    try:
        index, chosen = random_choice(options, weights)
        output = {
            "chosen": chosen,
            "index": index,
            "from_options": len(options),
        }
        if table_name:
            output["table"] = table_name
        
        return [TextContent(type="text", text=json.dumps(output))]
    
    except ValueError as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _handle_coin_flip(args: dict[str, Any]) -> list[TextContent]:
    """Handle coin flip."""
    result = _coin_flip()
    reason = args.get("reason", "")
    
    output = {"result": result}
    if reason:
        output["reason"] = reason
    
    return [TextContent(type="text", text=json.dumps(output))]


async def _handle_roll_stat_array(args: dict[str, Any]) -> list[TextContent]:
    """Generate a set of ability scores."""
    method = args.get("method", "4d6kh3")
    
    results = roll_multiple(method, 6)
    stats = [r.total for r in results]
    
    output = {
        "method": method,
        "stats": stats,
        "rolls": [
            {
                "kept": r.rolls,
                "dropped": r.dropped,
                "total": r.total,
            }
            for r in results
        ],
        "total": sum(stats),
        "suggestion": "Assign these values to your attributes as desired",
    }
    
    return [TextContent(type="text", text=json.dumps(output))]


async def _handle_percentile_roll(args: dict[str, Any]) -> list[TextContent]:
    """Roll a percentile die."""
    result = percentile()
    reason = args.get("reason", "")
    
    output = {"roll": result}
    if reason:
        output["reason"] = reason
    
    return [TextContent(type="text", text=json.dumps(output))]
