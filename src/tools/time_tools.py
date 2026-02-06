"""Time tools: get_game_time, set_game_time, advance_game_time.

Game time is stored in SECONDS from midnight Day 1.
- 1 minute = 60 seconds
- 1 hour = 3600 seconds
- 1 day = 86400 seconds
- Combat round (D&D 5e) = 6 seconds
"""

from typing import Any
from bson import ObjectId
from mcp.types import Tool, TextContent

from ..db import database

# Time constants
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400


def _format_game_time(seconds: int) -> str:
    """Convert game time (seconds from midnight day 1) to human readable format."""
    days = seconds // SECONDS_PER_DAY
    remaining = seconds % SECONDS_PER_DAY
    hours = remaining // SECONDS_PER_HOUR
    remaining = remaining % SECONDS_PER_HOUR
    minutes = remaining // SECONDS_PER_MINUTE
    secs = remaining % SECONDS_PER_MINUTE
    
    # Convert to 12-hour format
    period = "AM" if hours < 12 else "PM"
    display_hour = hours % 12
    if display_hour == 0:
        display_hour = 12
    
    # Include seconds only if non-zero (for combat precision)
    if secs > 0:
        time_str = f"{display_hour}:{minutes:02d}:{secs:02d} {period}"
    else:
        time_str = f"{display_hour}:{minutes:02d} {period}"
    
    day_str = f"Day {days + 1}"
    
    return f"{day_str}, {time_str}"


def get_tools() -> tuple[list[Tool], dict[str, callable]]:
    """Return tools and handlers for time management."""
    tools = [
            Tool(
                name="get_game_time",
                description="Get the current game time for a world. Time is stored in seconds for combat precision.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="set_game_time",
                description="Set the current game time for a world. Accepts seconds directly or use convenience params.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "seconds": {"type": "integer", "description": "Total seconds from midnight Day 1 (if setting absolute time)"},
                        "day": {"type": "integer", "description": "Day number (1-based)", "default": 1},
                        "hour": {"type": "integer", "description": "Hour (0-23)", "default": 0},
                        "minute": {"type": "integer", "description": "Minute (0-59)", "default": 0},
                        "second": {"type": "integer", "description": "Second (0-59)", "default": 0},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="advance_game_time",
                description="Move game time forward. Use seconds for combat (6s = 1 round), or minutes/hours/days for narrative time.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "seconds": {"type": "integer", "description": "Seconds to advance (default 0)", "default": 0},
                        "minutes": {"type": "integer", "description": "Minutes to advance (default 0)", "default": 0},
                        "hours": {"type": "integer", "description": "Hours to advance (default 0)", "default": 0},
                        "days": {"type": "integer", "description": "Days to advance (default 0)", "default": 0},
                        "rounds": {"type": "integer", "description": "Combat rounds to advance (1 round = 6 seconds)", "default": 0},
                    },
                    "required": ["world_id"],
                },
            ),
    ]
    
    handlers = {
        "get_game_time": _get_game_time,
        "set_game_time": _set_game_time,
        "advance_game_time": _advance_game_time,
    }
    
    return tools, handlers


async def _get_game_time(args: dict[str, Any]) -> list[TextContent]:
    """Get the current game time."""
    import json
    db = database.db
    
    doc = await db.worlds.find_one({"_id": ObjectId(args["world_id"])})
    if doc:
        game_time = doc.get("game_time", 0)
        formatted = _format_game_time(game_time)
        
        # Break down into components for convenience
        days = game_time // SECONDS_PER_DAY
        remaining = game_time % SECONDS_PER_DAY
        hours = remaining // SECONDS_PER_HOUR
        remaining = remaining % SECONDS_PER_HOUR
        minutes = remaining // SECONDS_PER_MINUTE
        seconds = remaining % SECONDS_PER_MINUTE
        
        result = {
            "world_id": args["world_id"],
            "game_time_seconds": game_time,
            "formatted": formatted,
            "breakdown": {
                "day": days + 1,  # 1-based for display
                "hour": hours,
                "minute": minutes,
                "second": seconds,
            }
        }
        return [TextContent(type="text", text=json.dumps(result))]
    return [TextContent(type="text", text=f"World {args['world_id']} not found")]


async def _set_game_time(args: dict[str, Any]) -> list[TextContent]:
    """Set the current game time."""
    import json
    db = database.db
    
    world_id = ObjectId(args["world_id"])
    
    # If absolute seconds provided, use that
    if "seconds" in args:
        new_time = args["seconds"]
    else:
        # Build from components (day is 1-based)
        day = args.get("day", 1) - 1  # Convert to 0-based
        hour = args.get("hour", 0)
        minute = args.get("minute", 0)
        second = args.get("second", 0)
        new_time = (day * SECONDS_PER_DAY) + (hour * SECONDS_PER_HOUR) + (minute * SECONDS_PER_MINUTE) + second
    
    await db.worlds.update_one(
        {"_id": world_id},
        {"$set": {"game_time": new_time}}
    )
    
    doc = await db.worlds.find_one({"_id": world_id})
    if doc:
        game_time = doc.get("game_time", 0)
        formatted = _format_game_time(game_time)
        result = {
            "world_id": args["world_id"],
            "game_time_seconds": game_time,
            "formatted": formatted,
        }
        return [TextContent(type="text", text=json.dumps(result))]
    return [TextContent(type="text", text=f"World {args['world_id']} not found")]


async def _advance_game_time(args: dict[str, Any]) -> list[TextContent]:
    """Advance game time by seconds, minutes, hours, days, or combat rounds."""
    import json
    db = database.db
    
    world_id = ObjectId(args["world_id"])
    
    # Calculate total seconds to advance
    seconds = args.get("seconds", 0)
    minutes = args.get("minutes", 0)
    hours = args.get("hours", 0)
    days = args.get("days", 0)
    rounds = args.get("rounds", 0)  # 1 combat round = 6 seconds
    
    total_seconds = (
        seconds +
        (minutes * SECONDS_PER_MINUTE) +
        (hours * SECONDS_PER_HOUR) +
        (days * SECONDS_PER_DAY) +
        (rounds * 6)
    )
    
    if total_seconds <= 0:
        return [TextContent(type="text", text='{"error": "Must advance by at least 1 second"}')]
    
    await db.worlds.update_one(
        {"_id": world_id},
        {"$inc": {"game_time": total_seconds}}
    )
    
    doc = await db.worlds.find_one({"_id": world_id})
    if doc:
        game_time = doc.get("game_time", 0)
        formatted = _format_game_time(game_time)
        result = {
            "world_id": args["world_id"],
            "game_time_seconds": game_time,
            "formatted": formatted,
            "advanced_by_seconds": total_seconds,
        }
        return [TextContent(type="text", text=json.dumps(result))]
    return [TextContent(type="text", text=f"World {args['world_id']} not found")]
