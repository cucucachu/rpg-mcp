"""Shared utilities for MCP tools."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_world_game_time(db: "AsyncIOMotorDatabase", world_id: str) -> int:
    """Derive current game time from events (and chronicles as fallback).
    
    Game time is now tracked via events. The "current" game time is the highest
    game_time across all events, or the latest chronicle's game_time_end if no events.
    """
    # Highest game_time from events
    max_event = await db.events.find_one(
        {"world_id": world_id},
        {"game_time": 1},
        sort=[("game_time", -1)],
    )
    max_event_time = max_event.get("game_time", 0) if max_event else 0
    
    # Latest chronicle's game_time_end (for worlds with chronicles but no recent events)
    last_chronicle = await db.chronicles.find_one(
        {"world_id": world_id},
        {"game_time_end": 1},
        sort=[("_id", -1)],
    )
    chronicle_end = last_chronicle.get("game_time_end") or 0 if last_chronicle else 0
    
    return max(max_event_time, chronicle_end)
