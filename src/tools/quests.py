"""Quest and Story tools: create_quest, delete_quest, begin_quest, update_quest, complete_quest,
record_event, delete_event, set_chronicle."""

from typing import Any
from bson import ObjectId
from mcp.types import Tool, TextContent

from ..db import database
from ..models import Quest, Event, Chronicle
from ..models.quest import RelatedEntity


def get_tools() -> tuple[list[Tool], dict[str, callable]]:
    """Return tools and handlers for quest and story management."""
    tools = [
            Tool(
                name="create_quest",
                description="Create a new quest",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "name": {"type": "string", "description": "Quest name"},
                        "description": {"type": "string", "description": "Quest description"},
                        "giver_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                        "objectives": {"type": "string", "description": "Quest objectives"},
                        "rewards": {"type": "string", "description": "Quest rewards"},
                        "time_limit": {"type": "integer", "description": "Time limit in game seconds"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["world_id", "name"],
                },
            ),
            Tool(
                name="delete_quest",
                description="Remove a quest",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "quest_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["quest_id"],
                },
            ),
            Tool(
                name="begin_quest",
                description="Assign a quest to a character",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "quest_id": {"type": "string", "description": "24-char hex string ID"},
                        "character_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                    },
                    "required": ["quest_id", "character_id"],
                },
            ),
            Tool(
                name="update_quest",
                description="Update quest progress or objectives",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "quest_id": {"type": "string", "description": "24-char hex string ID"},
                        "objectives": {"type": "string", "description": "Updated objectives"},
                        "progress": {"type": "string", "description": "Progress description"},
                        "description": {"type": "string", "description": "Updated description"},
                    },
                    "required": ["quest_id"],
                },
            ),
            Tool(
                name="complete_quest",
                description="Mark a quest as finished",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "quest_id": {"type": "string", "description": "24-char hex string ID"},
                        "status": {"type": "string", "description": "Completion status (success, failed, abandoned, etc.)"},
                    },
                    "required": ["quest_id", "status"],
                },
            ),
            Tool(
                name="record_event",
                description="Log a game event (state change, action, etc.). Game time tracks the narrative timeline.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "game_time": {"type": "integer", "description": "Game time in SECONDS since Day 1 00:00:00 (e.g., 3600=1hr, 86400=1day). Estimate based on event duration."},
                        "name": {"type": "string", "description": "Event name/summary"},
                        "description": {"type": "string", "description": "Detailed event description"},
                        "location_id": {"type": "string", "description": "24-char hex string ID"},
                        "participants": {"type": "string", "description": "Who was involved"},
                        "changes": {"type": "string", "description": "What changed"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["world_id", "name", "description", "game_time"],
                },
            ),
            Tool(
                name="delete_event",
                description="Remove an event record",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["event_id"],
                },
            ),
            Tool(
                name="set_chronicle",
                description="Create, update, or delete a chronicle (story summary). Use start_event_id/end_event_id to auto-link events in that ID range.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "24-char hex string ID (omit to create new)"},
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "title": {"type": "string", "description": "Chronicle title"},
                        "summary": {"type": "string", "description": "Story summary"},
                        "game_time_start": {"type": "integer", "description": "When this story beat started (seconds)"},
                        "game_time_end": {"type": "integer", "description": "When it ended (seconds)"},
                        "significance": {"type": "string", "description": "major, minor, turning_point"},
                        "related_events": {"type": "array", "items": {"type": "string"}, "description": "Event IDs (manual)"},
                        "start_event_id": {"type": "string", "description": "24-char hex string ID - link all events from this ID onwards"},
                        "end_event_id": {"type": "string", "description": "24-char hex string ID - link all events up to and including this ID"},
                        "link_events_in_range": {"type": "boolean", "description": "DEPRECATED: Use start_event_id/end_event_id instead", "default": False},
                        "related_entities": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "entity_type": {"type": "string"},
                                    "entity_id": {"type": "string"},
                                },
                            },
                        },
                        "consequences": {"type": "string", "description": "What changed as a result"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "delete": {"type": "boolean", "default": False},
                    },
                    "required": [],
                },
            ),
    ]
    
    handlers = {
        "create_quest": _create_quest,
        "delete_quest": _delete_quest,
        "begin_quest": _begin_quest,
        "update_quest": _update_quest,
        "complete_quest": _complete_quest,
        "record_event": _record_event,
        "delete_event": _delete_event,
        "set_chronicle": _set_chronicle,
    }
    
    return tools, handlers


async def _create_quest(args: dict[str, Any]) -> list[TextContent]:
    """Create a new quest."""
    db = database.db
    
    quest = Quest(
        world_id=args["world_id"],
        name=args["name"],
        description=args.get("description", ""),
        status="available",
        giver_id=args.get("giver_id"),
        objectives=args.get("objectives", ""),
        rewards=args.get("rewards", ""),
        time_limit=args.get("time_limit"),
        tags=args.get("tags", []),
    )
    
    result = await db.quests.insert_one(quest.to_doc())
    quest.id = str(result.inserted_id)
    
    return [TextContent(type="text", text=f"Created quest: {quest.model_dump_json()}")]


async def _delete_quest(args: dict[str, Any]) -> list[TextContent]:
    """Delete a quest."""
    db = database.db
    
    result = await db.quests.delete_one({"_id": ObjectId(args["quest_id"])})
    if result.deleted_count:
        return [TextContent(type="text", text=f"Deleted quest {args['quest_id']}")]
    return [TextContent(type="text", text=f"Quest {args['quest_id']} not found")]


async def _begin_quest(args: dict[str, Any]) -> list[TextContent]:
    """Assign a quest to a character."""
    db = database.db
    
    quest_id = ObjectId(args["quest_id"])
    character_id = args["character_id"]
    
    # Add character to assigned_to and set status to active
    await db.quests.update_one(
        {"_id": quest_id},
        {
            "$addToSet": {"assigned_to": character_id},
            "$set": {"status": "active"}
        }
    )
    
    doc = await db.quests.find_one({"_id": quest_id})
    if doc:
        quest = Quest.from_doc(doc)
        return [TextContent(type="text", text=f"Quest begun: {quest.model_dump_json()}")]
    return [TextContent(type="text", text=f"Quest {args['quest_id']} not found")]


async def _update_quest(args: dict[str, Any]) -> list[TextContent]:
    """Update quest progress."""
    db = database.db
    
    quest_id = ObjectId(args["quest_id"])
    
    update_data = {}
    for field in ["objectives", "progress", "description"]:
        if field in args:
            update_data[field] = args[field]
    
    if update_data:
        await db.quests.update_one({"_id": quest_id}, {"$set": update_data})
    
    doc = await db.quests.find_one({"_id": quest_id})
    if doc:
        quest = Quest.from_doc(doc)
        return [TextContent(type="text", text=f"Updated quest: {quest.model_dump_json()}")]
    return [TextContent(type="text", text=f"Quest {args['quest_id']} not found")]


async def _complete_quest(args: dict[str, Any]) -> list[TextContent]:
    """Mark a quest as complete."""
    db = database.db
    
    quest_id = ObjectId(args["quest_id"])
    
    await db.quests.update_one(
        {"_id": quest_id},
        {"$set": {"status": args["status"]}}
    )
    
    doc = await db.quests.find_one({"_id": quest_id})
    if doc:
        quest = Quest.from_doc(doc)
        return [TextContent(type="text", text=f"Completed quest: {quest.model_dump_json()}")]
    return [TextContent(type="text", text=f"Quest {args['quest_id']} not found")]


async def _record_event(args: dict[str, Any]) -> list[TextContent]:
    """Record a game event."""
    db = database.db
    
    # Get game_time - fallback to last event's time if not provided
    game_time = args.get("game_time")
    if game_time is None:
        # Find the most recent event for this world
        last_event = await db.events.find_one(
            {"world_id": args["world_id"]},
            sort=[("_id", -1)]
        )
        if last_event:
            game_time = last_event.get("game_time", 0)
        else:
            game_time = 0
    
    event = Event(
        world_id=args["world_id"],
        game_time=game_time,
        name=args["name"],
        description=args["description"],
        location_id=args.get("location_id"),
        participants=args.get("participants", ""),
        changes=args.get("changes", ""),
        tags=args.get("tags", []),
    )
    
    result = await db.events.insert_one(event.to_doc())
    event.id = str(result.inserted_id)
    
    return [TextContent(type="text", text=f"Recorded event: {event.model_dump_json()}")]


async def _delete_event(args: dict[str, Any]) -> list[TextContent]:
    """Delete an event."""
    db = database.db
    
    result = await db.events.delete_one({"_id": ObjectId(args["event_id"])})
    if result.deleted_count:
        return [TextContent(type="text", text=f"Deleted event {args['event_id']}")]
    return [TextContent(type="text", text=f"Event {args['event_id']} not found")]


async def _set_chronicle(args: dict[str, Any]) -> list[TextContent]:
    """Create, update, or delete a chronicle."""
    db = database.db
    
    # Delete
    if args.get("delete") and args.get("id"):
        result = await db.chronicles.delete_one({"_id": ObjectId(args["id"])})
        if result.deleted_count:
            return [TextContent(type="text", text=f"Deleted chronicle {args['id']}")]
        return [TextContent(type="text", text=f"Chronicle {args['id']} not found")]
    
    chronicle_id = args.get("id")
    
    # Parse related entities
    related_entities = [
        RelatedEntity(**e) for e in args.get("related_entities", [])
    ]
    
    related_events = args.get("related_events", [])
    
    # Auto-link events by ID range (preferred method)
    start_event_id = args.get("start_event_id")
    end_event_id = args.get("end_event_id")
    world_id = args.get("world_id")
    
    if start_event_id or end_event_id:
        # Build query for event ID range
        query = {"world_id": world_id} if world_id else {}
        id_filter = {}
        
        if start_event_id:
            id_filter["$gte"] = ObjectId(start_event_id)
        if end_event_id:
            id_filter["$lte"] = ObjectId(end_event_id)
        
        if id_filter:
            query["_id"] = id_filter
        
        # Find events in the ID range
        events_cursor = db.events.find(query).sort("_id", 1)
        async for event_doc in events_cursor:
            event_id = str(event_doc["_id"])
            if event_id not in related_events:
                related_events.append(event_id)
    
    # Legacy: Auto-link events in time range if requested (deprecated)
    elif args.get("link_events_in_range"):
        time_start = args.get("game_time_start")
        time_end = args.get("game_time_end")
        
        # If updating, get world_id and times from existing chronicle if not provided
        if chronicle_id and (not world_id or time_start is None):
            existing = await db.chronicles.find_one({"_id": ObjectId(chronicle_id)})
            if existing:
                world_id = world_id or existing.get("world_id")
                time_start = time_start if time_start is not None else existing.get("game_time_start")
                time_end = time_end if time_end is not None else existing.get("game_time_end")
        
        if world_id and time_start is not None:
            query = {
                "world_id": world_id,
                "game_time": {"$gte": time_start}
            }
            if time_end is not None:
                query["game_time"]["$lte"] = time_end
            
            events_cursor = db.events.find(query).sort("game_time", 1)
            async for event_doc in events_cursor:
                event_id = str(event_doc["_id"])
                if event_id not in related_events:
                    related_events.append(event_id)
    
    if chronicle_id:
        # Update existing
        update_data = {}
        for field in ["world_id", "title", "summary", "game_time_start", "game_time_end", 
                      "significance", "consequences", "tags"]:
            if field in args:
                update_data[field] = args[field]
        
        # Always update related_events if we processed them
        if args.get("start_event_id") or args.get("end_event_id") or args.get("link_events_in_range") or "related_events" in args:
            update_data["related_events"] = related_events
        
        if "related_entities" in args:
            update_data["related_entities"] = [e.model_dump() for e in related_entities]
        
        if update_data:
            await db.chronicles.update_one(
                {"_id": ObjectId(chronicle_id)},
                {"$set": update_data}
            )
        
        doc = await db.chronicles.find_one({"_id": ObjectId(chronicle_id)})
        chronicle = Chronicle.from_doc(doc)
        return [TextContent(type="text", text=f"Updated chronicle: {chronicle.model_dump_json()}")]
    else:
        # Create new
        chronicle = Chronicle(
            world_id=args["world_id"],
            title=args.get("title", ""),
            summary=args.get("summary", ""),
            game_time_start=args.get("game_time_start", 0),
            game_time_end=args.get("game_time_end"),
            significance=args.get("significance", ""),
            related_events=related_events,
            related_entities=related_entities,
            consequences=args.get("consequences", ""),
            tags=args.get("tags", []),
        )
        result = await db.chronicles.insert_one(chronicle.to_doc())
        chronicle.id = str(result.inserted_id)
        return [TextContent(type="text", text=f"Created chronicle: {chronicle.model_dump_json()}")]
