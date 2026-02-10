"""Query tools: get_entity, find_characters, find_items, find_locations, search_locations, find_nearby_locations,
find_quests, find_events, search_lore, find_factions, find_parties, get_world_summary, get_location_contents."""

from typing import Any
from bson import ObjectId
from mcp.types import Tool, TextContent
import json

from ..db import database
from ..utils import get_world_game_time
from ..models import (
    World, Character, Item, ItemTemplate, AbilityTemplate,
    Location, Faction, Party, Quest, Event, Chronicle, Lore
)


# Map collection names to their model classes
COLLECTION_MAP = {
    "world": ("worlds", World),
    "character": ("characters", Character),
    "item": ("items", Item),
    "item_template": ("item_templates", ItemTemplate),
    "ability_template": ("ability_templates", AbilityTemplate),
    "location": ("locations", Location),
    "faction": ("factions", Faction),
    "party": ("parties", Party),
    "quest": ("quests", Quest),
    "event": ("events", Event),
    "chronicle": ("chronicles", Chronicle),
    "lore": ("lore", Lore),
}


def get_tools() -> tuple[list[Tool], dict[str, callable]]:
    """Return tools and handlers for queries."""
    tools = [
            Tool(
                name="get_entity",
                description="Fetch any entity by ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "collection": {
                            "type": "string",
                            "description": "Collection name",
                            "enum": list(COLLECTION_MAP.keys()),
                        },
                        "id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["collection", "id"],
                },
            ),
            Tool(
                name="find_characters",
                description="Search for characters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "location_id": {"type": "string", "description": "24-char hex string ID"},
                        "faction_id": {"type": "string", "description": "24-char hex string ID"},
                        "is_player_character": {"type": "boolean", "description": "Filter PCs/NPCs"},
                        "name": {"type": "string", "description": "Filter by name (partial match)"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                        "limit": {"type": "integer", "description": "Max results", "default": 50},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="find_items",
                description="Search for items",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "owner_id": {"type": "string", "description": "24-char hex string ID"},
                        "location_id": {"type": "string", "description": "24-char hex string ID"},
                        "template_id": {"type": "string", "description": "24-char hex string ID"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                        "limit": {"type": "integer", "description": "Max results", "default": 50},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="find_locations",
                description="Search for locations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "parent_location_id": {"type": "string", "description": "24-char hex string ID"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                        "limit": {"type": "integer", "description": "Max results", "default": 50},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="find_nearby_locations",
                description="Find locations near a point",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "x": {"type": "number", "description": "X coordinate"},
                        "y": {"type": "number", "description": "Y coordinate"},
                        "distance": {"type": "number", "description": "Max distance"},
                    },
                    "required": ["world_id", "x", "y", "distance"],
                },
            ),
            Tool(
                name="search_locations",
                description="Search for locations by name or description using text matching. Use this when you need to find a location by what it's called or what it contains.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "query": {"type": "string", "description": "Search text to match against location name or description"},
                        "limit": {"type": "integer", "description": "Max results", "default": 20},
                    },
                    "required": ["world_id", "query"],
                },
            ),
            Tool(
                name="find_quests",
                description="Search for quests",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "status": {"type": "string", "description": "Filter by status"},
                        "assigned_to": {"type": "string", "description": "Filter by assigned character"},
                        "giver_id": {"type": "string", "description": "24-char hex string ID"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                        "limit": {"type": "integer", "description": "Max results", "default": 50},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="find_events",
                description="Search the timeline for events",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "time_start": {"type": "integer", "description": "Filter from this time"},
                        "time_end": {"type": "integer", "description": "Filter to this time"},
                        "location_id": {"type": "string", "description": "24-char hex string ID"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                        "limit": {"type": "integer", "description": "Max results", "default": 50},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="search_lore",
                description="Search through lore entries by keyword. Supports full-text search (default) and regex modes. Use for finding information about people, places, events, history, etc.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "query": {"type": "string", "description": "Search query (keywords for text mode, pattern for regex)"},
                        "mode": {"type": "string", "description": "Search mode: 'text' (default), 'regex', or 'both' (text first, then regex fallback)", "default": "both", "enum": ["text", "regex", "both"]},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                        "limit": {"type": "integer", "description": "Max results", "default": 20},
                    },
                    "required": ["world_id", "query"],
                },
            ),
            Tool(
                name="find_factions",
                description="Search for factions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "type": {"type": "string", "description": "Filter by faction type"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                        "limit": {"type": "integer", "description": "Max results", "default": 50},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="find_parties",
                description="Search for parties",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "member_id": {"type": "string", "description": "24-char hex string ID"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                        "limit": {"type": "integer", "description": "Max results", "default": 50},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="get_world_summary",
                description="Get a quick overview of a world's current state",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="get_location_contents",
                description="Get characters and items at a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["location_id"],
                },
            ),
            Tool(
                name="load_session",
                description="Load all context needed to resume a game session. Returns world, PCs, active quests, recent chronicles, and recent events. Use entity IDs to drill down for more detail.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "chronicle_limit": {"type": "integer", "description": "Max chronicles to return", "default": 3},
                        "event_limit": {"type": "integer", "description": "Max recent events to return", "default": 10},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="get_character_inventory",
                description="Get all items owned by a character",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                    },
                    "required": ["character_id"],
                },
            ),
            Tool(
                name="get_chronicle_details",
                description="Get a chronicle with its related events expanded. Useful for drilling into what happened during a session or story beat.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "chronicle_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["chronicle_id"],
                },
            ),
    ]
    
    handlers = {
        "get_entity": _get_entity,
        "find_characters": _find_characters,
        "find_items": _find_items,
        "find_locations": _find_locations,
        "find_nearby_locations": _find_nearby_locations,
        "search_locations": _search_locations,
        "find_quests": _find_quests,
        "find_events": _find_events,
        "search_lore": _search_lore,
        "find_factions": _find_factions,
        "find_parties": _find_parties,
        "get_world_summary": _get_world_summary,
        "get_location_contents": _get_location_contents,
        "load_session": _load_session,
        "get_character_inventory": _get_character_inventory,
        "get_chronicle_details": _get_chronicle_details,
    }
    
    return tools, handlers


async def _get_entity(args: dict[str, Any]) -> list[TextContent]:
    """Fetch any entity by ID."""
    db = database.db
    
    collection_name, model_class = COLLECTION_MAP.get(args["collection"], (None, None))
    if not collection_name:
        return [TextContent(type="text", text=f"Unknown collection: {args['collection']}")]
    
    collection = db[collection_name]
    doc = await collection.find_one({"_id": ObjectId(args["id"])})
    
    if doc:
        entity = model_class.from_doc(doc)
        return [TextContent(type="text", text=entity.model_dump_json())]
    return [TextContent(type="text", text=f"{args['collection']} {args['id']} not found")]


async def _find_characters(args: dict[str, Any]) -> list[TextContent]:
    """Search for characters."""
    db = database.db
    
    query = {"world_id": args["world_id"]}
    
    if "location_id" in args:
        query["location_id"] = args["location_id"]
    if "faction_id" in args:
        query["factions.faction_id"] = args["faction_id"]
    if "is_player_character" in args:
        query["is_player_character"] = args["is_player_character"]
    if "name" in args:
        query["name"] = {"$regex": args["name"], "$options": "i"}
    if "tags" in args and args["tags"]:
        query["tags"] = {"$all": args["tags"]}
    
    limit = args.get("limit", 50)
    cursor = db.characters.find(query).limit(limit)
    
    results = []
    async for doc in cursor:
        results.append(Character.from_doc(doc).model_dump())
    
    return [TextContent(type="text", text=json.dumps(results))]


async def _find_items(args: dict[str, Any]) -> list[TextContent]:
    """Search for items."""
    db = database.db
    
    query = {"world_id": args["world_id"]}
    
    if "owner_id" in args:
        query["owner_id"] = args["owner_id"]
    if "location_id" in args:
        query["location_id"] = args["location_id"]
    if "template_id" in args:
        query["template_id"] = args["template_id"]
    if "tags" in args and args["tags"]:
        query["tags"] = {"$all": args["tags"]}
    
    limit = args.get("limit", 50)
    cursor = db.items.find(query).limit(limit)
    
    results = []
    async for doc in cursor:
        results.append(Item.from_doc(doc).model_dump())
    
    return [TextContent(type="text", text=json.dumps(results))]


async def _find_locations(args: dict[str, Any]) -> list[TextContent]:
    """Search for locations."""
    db = database.db
    
    query = {"world_id": args["world_id"]}
    
    if "parent_location_id" in args:
        query["parent_location_id"] = args["parent_location_id"]
    if "tags" in args and args["tags"]:
        query["tags"] = {"$all": args["tags"]}
    
    limit = args.get("limit", 50)
    cursor = db.locations.find(query).limit(limit)
    
    results = []
    async for doc in cursor:
        results.append(Location.from_doc(doc).model_dump())
    
    return [TextContent(type="text", text=json.dumps(results))]


async def _find_nearby_locations(args: dict[str, Any]) -> list[TextContent]:
    """Find locations near a point."""
    db = database.db
    
    query = {
        "world_id": args["world_id"],
        "coordinates": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [args["x"], args["y"]]
                },
                "$maxDistance": args["distance"]
            }
        }
    }
    
    cursor = db.locations.find(query)
    
    results = []
    async for doc in cursor:
        results.append(Location.from_doc(doc).model_dump())
    
    return [TextContent(type="text", text=json.dumps(results))]


async def _search_locations(args: dict[str, Any]) -> list[TextContent]:
    """Search for locations by name or description using regex."""
    db = database.db
    
    search_query = args["query"]
    regex_pattern = {"$regex": search_query, "$options": "i"}
    
    query = {
        "world_id": args["world_id"],
        "$or": [
            {"name": regex_pattern},
            {"description": regex_pattern},
        ]
    }
    
    limit = args.get("limit", 20)
    cursor = db.locations.find(query).limit(limit)
    
    results = []
    async for doc in cursor:
        results.append(Location.from_doc(doc).model_dump())
    
    return [TextContent(type="text", text=json.dumps(results))]


async def _find_quests(args: dict[str, Any]) -> list[TextContent]:
    """Search for quests."""
    db = database.db
    
    query = {"world_id": args["world_id"]}
    
    if "status" in args:
        query["status"] = args["status"]
    if "assigned_to" in args:
        query["assigned_to"] = args["assigned_to"]
    if "giver_id" in args:
        query["giver_id"] = args["giver_id"]
    if "tags" in args and args["tags"]:
        query["tags"] = {"$all": args["tags"]}
    
    limit = args.get("limit", 50)
    cursor = db.quests.find(query).limit(limit)
    
    results = []
    async for doc in cursor:
        results.append(Quest.from_doc(doc).model_dump())
    
    return [TextContent(type="text", text=json.dumps(results))]


async def _find_events(args: dict[str, Any]) -> list[TextContent]:
    """Search timeline events."""
    db = database.db
    
    query = {"world_id": args["world_id"]}
    
    if "time_start" in args or "time_end" in args:
        query["game_time"] = {}
        if "time_start" in args:
            query["game_time"]["$gte"] = args["time_start"]
        if "time_end" in args:
            query["game_time"]["$lte"] = args["time_end"]
    if "location_id" in args:
        query["location_id"] = args["location_id"]
    if "tags" in args and args["tags"]:
        query["tags"] = {"$all": args["tags"]}
    
    limit = args.get("limit", 50)
    cursor = db.events.find(query).sort("game_time", -1).limit(limit)
    
    results = []
    async for doc in cursor:
        results.append(Event.from_doc(doc).model_dump())
    
    return [TextContent(type="text", text=json.dumps(results))]


async def _search_lore(args: dict[str, Any]) -> list[TextContent]:
    """Full-text search through lore with regex fallback."""
    db = database.db
    
    world_id = args["world_id"]
    search_query = args["query"]
    limit = args.get("limit", 20)
    search_mode = args.get("mode", "text")  # text, regex, or both
    
    results = []
    
    # Try text search first (unless mode is regex-only)
    if search_mode in ("text", "both"):
        query = {
            "world_id": world_id,
            "$text": {"$search": search_query}
        }
        
        if "tags" in args and args["tags"]:
            query["tags"] = {"$all": args["tags"]}
        
        try:
            cursor = db.lore.find(
                query,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            async for doc in cursor:
                lore = Lore.from_doc(doc)
                results.append({
                    **lore.model_dump(),
                    "match_type": "text",
                })
        except Exception:
            # Text search might fail if index doesn't exist
            pass
    
    # If no results or mode is regex, try regex search
    if (not results and search_mode == "both") or search_mode == "regex":
        # Case-insensitive regex search on title and content
        regex_pattern = {"$regex": search_query, "$options": "i"}
        query = {
            "world_id": world_id,
            "$or": [
                {"title": regex_pattern},
                {"content": regex_pattern},
            ]
        }
        
        if "tags" in args and args["tags"]:
            query["tags"] = {"$all": args["tags"]}
        
        seen_ids = {r["id"] for r in results}
        cursor = db.lore.find(query).limit(limit - len(results))
        
        async for doc in cursor:
            lore = Lore.from_doc(doc)
            if lore.id not in seen_ids:
                results.append({
                    **lore.model_dump(),
                    "match_type": "regex",
                })
    
    output = {
        "query": search_query,
        "mode": search_mode,
        "results": results,
        "count": len(results),
    }
    
    return [TextContent(type="text", text=json.dumps(output))]


async def _find_factions(args: dict[str, Any]) -> list[TextContent]:
    """Search for factions."""
    db = database.db
    
    query = {"world_id": args["world_id"]}
    
    if "type" in args:
        query["type"] = args["type"]
    if "tags" in args and args["tags"]:
        query["tags"] = {"$all": args["tags"]}
    
    limit = args.get("limit", 50)
    cursor = db.factions.find(query).limit(limit)
    
    results = []
    async for doc in cursor:
        results.append(Faction.from_doc(doc).model_dump())
    
    return [TextContent(type="text", text=json.dumps(results))]


async def _find_parties(args: dict[str, Any]) -> list[TextContent]:
    """Search for parties."""
    db = database.db
    
    query = {"world_id": args["world_id"]}
    
    if "member_id" in args:
        query["members"] = args["member_id"]
    if "tags" in args and args["tags"]:
        query["tags"] = {"$all": args["tags"]}
    
    limit = args.get("limit", 50)
    cursor = db.parties.find(query).limit(limit)
    
    results = []
    async for doc in cursor:
        results.append(Party.from_doc(doc).model_dump())
    
    return [TextContent(type="text", text=json.dumps(results))]


async def _get_world_summary(args: dict[str, Any]) -> list[TextContent]:
    """Get a quick overview of a world."""
    db = database.db
    
    world_id = args["world_id"]
    
    # Get world info
    world_doc = await db.worlds.find_one({"_id": ObjectId(world_id)})
    if not world_doc:
        return [TextContent(type="text", text=f"World {world_id} not found")]
    
    world = World.from_doc(world_doc)
    
    # Get counts
    character_count = await db.characters.count_documents({"world_id": world_id})
    pc_count = await db.characters.count_documents({"world_id": world_id, "is_player_character": True})
    location_count = await db.locations.count_documents({"world_id": world_id})
    item_count = await db.items.count_documents({"world_id": world_id})
    
    # Get active quests
    active_quests_cursor = db.quests.find({"world_id": world_id, "status": "active"}).limit(10)
    active_quests = []
    async for doc in active_quests_cursor:
        active_quests.append({"id": str(doc["_id"]), "name": doc.get("name", "")})
    
    # Get parties
    parties_cursor = db.parties.find({"world_id": world_id}).limit(10)
    parties = []
    async for doc in parties_cursor:
        parties.append({"id": str(doc["_id"]), "name": doc.get("name", ""), "member_count": len(doc.get("members", []))})
    
    # Get recent chronicles
    chronicles_cursor = db.chronicles.find({"world_id": world_id}).sort("game_time_start", -1).limit(5)
    recent_chronicles = []
    async for doc in chronicles_cursor:
        recent_chronicles.append({"id": str(doc["_id"]), "title": doc.get("title", "")})
    
    game_time = await get_world_game_time(db, world_id)
    summary = {
        "world": world.model_dump(),
        "game_time": game_time,
        "counts": {
            "characters": character_count,
            "player_characters": pc_count,
            "npcs": character_count - pc_count,
            "locations": location_count,
            "items": item_count,
        },
        "active_quests": active_quests,
        "parties": parties,
        "recent_chronicles": recent_chronicles,
    }
    
    return [TextContent(type="text", text=json.dumps(summary))]


async def _get_location_contents(args: dict[str, Any]) -> list[TextContent]:
    """Get characters and items at a location."""
    db = database.db
    
    location_id = args["location_id"]
    
    # Get location info
    location_doc = await db.locations.find_one({"_id": ObjectId(location_id)})
    if not location_doc:
        return [TextContent(type="text", text=f"Location {location_id} not found")]
    
    location = Location.from_doc(location_doc)
    
    # Get characters at location
    characters_cursor = db.characters.find({"location_id": location_id})
    characters = []
    async for doc in characters_cursor:
        characters.append(Character.from_doc(doc).model_dump())
    
    # Get items at location
    items_cursor = db.items.find({"location_id": location_id})
    items = []
    async for doc in items_cursor:
        items.append(Item.from_doc(doc).model_dump())
    
    result = {
        "location": location.model_dump(),
        "characters": characters,
        "items": items,
    }
    
    return [TextContent(type="text", text=json.dumps(result))]


def _format_game_time(seconds: int) -> str:
    """Convert game time (seconds from midnight day 1) to human readable format."""
    SECONDS_PER_MINUTE = 60
    SECONDS_PER_HOUR = 3600
    SECONDS_PER_DAY = 86400
    
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


async def _load_session(args: dict[str, Any]) -> list[TextContent]:
    """Load all context needed to resume a game session."""
    db = database.db
    
    world_id = args["world_id"]
    chronicle_limit = args.get("chronicle_limit", 3)
    event_limit = args.get("event_limit", 10)
    
    # Get world
    world_doc = await db.worlds.find_one({"_id": ObjectId(world_id)})
    if not world_doc:
        return [TextContent(type="text", text=f"World {world_id} not found")]
    
    world = World.from_doc(world_doc)
    
    # Get all player characters with summary info
    pc_cursor = db.characters.find({"world_id": world_id, "is_player_character": True})
    player_characters = []
    location_ids_to_fetch = set()
    
    async for doc in pc_cursor:
        char = Character.from_doc(doc)
        if char.location_id:
            location_ids_to_fetch.add(char.location_id)
        
        # Extract HP from attributes if present
        hp_current = None
        hp_max = None
        for attr in char.attributes:
            if attr.name.upper() == "HP":
                hp_current = attr.value
                hp_max = attr.max
                break
        
        player_characters.append({
            "id": char.id,
            "name": char.name,
            "description": char.description,
            "level": char.level,
            "hp_current": hp_current,
            "hp_max": hp_max,
            "location_id": char.location_id,
            "statuses": [{"name": s.name, "description": s.description} for s in char.statuses],
            "ability_count": len(char.abilities),
        })
    
    # Resolve PC location names
    location_names = {}
    for loc_id in location_ids_to_fetch:
        loc_doc = await db.locations.find_one({"_id": ObjectId(loc_id)})
        if loc_doc:
            location_names[loc_id] = loc_doc.get("name", "Unknown")
    
    # Add location names to PCs
    for pc in player_characters:
        if pc["location_id"]:
            pc["location_name"] = location_names.get(pc["location_id"], "Unknown")
    
    # Get active quests
    quest_cursor = db.quests.find({"world_id": world_id, "status": "active"})
    active_quests = []
    async for doc in quest_cursor:
        quest = Quest.from_doc(doc)
        active_quests.append({
            "id": quest.id,
            "name": quest.name,
            "description": quest.description,
            "status": quest.status,
            "progress": quest.progress,
            "assigned_to": quest.assigned_to,
            "giver_id": quest.giver_id,
        })
    
    # Get recent chronicles (most recent first)
    chronicle_cursor = db.chronicles.find({"world_id": world_id}).sort("game_time_end", -1).limit(chronicle_limit)
    recent_chronicles = []
    async for doc in chronicle_cursor:
        chron = Chronicle.from_doc(doc)
        recent_chronicles.append({
            "id": chron.id,
            "title": chron.title,
            "summary": chron.summary,
            "consequences": chron.consequences,
            "game_time_start": chron.game_time_start,
            "game_time_end": chron.game_time_end,
            "significance": chron.significance,
        })
    
    # Get recent events (most recent first)
    event_cursor = db.events.find({"world_id": world_id}).sort("game_time", -1).limit(event_limit)
    recent_events = []
    async for doc in event_cursor:
        event = Event.from_doc(doc)
        recent_events.append({
            "id": event.id,
            "description": event.description,
            "game_time": event.game_time,
            "location_id": event.location_id,
            "participants": event.participants,
        })
    
    # Get parties that include any PC
    pc_ids = [pc["id"] for pc in player_characters]
    party_cursor = db.parties.find({"world_id": world_id, "members": {"$in": pc_ids}})
    parties = []
    async for doc in party_cursor:
        party = Party.from_doc(doc)
        parties.append({
            "id": party.id,
            "name": party.name,
            "leader_id": party.leader_id,
            "members": party.members,
        })
    
    game_time = await get_world_game_time(db, world_id)
    session = {
        "world": {
            "id": world.id,
            "name": world.name,
            "description": world.description,
            "settings": world.settings,
        },
        "game_time": {
            "raw": game_time,
            "formatted": _format_game_time(game_time),
        },
        "player_characters": player_characters,
        "active_quests": active_quests,
        "recent_chronicles": recent_chronicles,
        "recent_events": recent_events,
        "parties": parties,
        "counts": {
            "total_characters": await db.characters.count_documents({"world_id": world_id}),
            "total_locations": await db.locations.count_documents({"world_id": world_id}),
            "total_items": await db.items.count_documents({"world_id": world_id}),
        },
    }
    
    return [TextContent(type="text", text=json.dumps(session))]


async def _get_character_inventory(args: dict[str, Any]) -> list[TextContent]:
    """Get all items owned by a character."""
    db = database.db
    
    character_id = args["character_id"]
    
    # Verify character exists
    char_doc = await db.characters.find_one({"_id": ObjectId(character_id)})
    if not char_doc:
        return [TextContent(type="text", text=f"Character {character_id} not found")]
    
    char = Character.from_doc(char_doc)
    
    # Get all items owned by this character
    items_cursor = db.items.find({"owner_id": character_id})
    items = []
    async for doc in items_cursor:
        item = Item.from_doc(doc)
        items.append({
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "quantity": item.quantity,
            "statuses": [{"name": s.name, "description": s.description} for s in item.statuses],
            "attributes": [{"name": a.name, "value": a.value} for a in item.attributes],
            "tags": item.tags,
        })
    
    result = {
        "character_id": character_id,
        "character_name": char.name,
        "items": items,
        "total_items": len(items),
    }
    
    return [TextContent(type="text", text=json.dumps(result))]


async def _get_chronicle_details(args: dict[str, Any]) -> list[TextContent]:
    """Get a chronicle with its related events expanded."""
    db = database.db
    
    chronicle_id = args["chronicle_id"]
    
    # Get the chronicle
    chronicle_doc = await db.chronicles.find_one({"_id": ObjectId(chronicle_id)})
    if not chronicle_doc:
        return [TextContent(type="text", text=f"Chronicle {chronicle_id} not found")]
    
    chronicle = Chronicle.from_doc(chronicle_doc)
    
    # Fetch all related events
    events = []
    for event_id in chronicle.related_events:
        try:
            event_doc = await db.events.find_one({"_id": ObjectId(event_id)})
            if event_doc:
                event = Event.from_doc(event_doc)
                events.append({
                    "id": event.id,
                    "name": event.name,
                    "description": event.description,
                    "game_time": event.game_time,
                    "formatted_time": _format_game_time(event.game_time),
                    "location_id": event.location_id,
                    "participants": event.participants,
                    "tags": event.tags,
                })
        except Exception:
            # Skip invalid event IDs
            pass
    
    # Sort events by time
    events.sort(key=lambda e: e["game_time"])
    
    result = {
        "chronicle": {
            "id": chronicle.id,
            "title": chronicle.title,
            "summary": chronicle.summary,
            "game_time_start": chronicle.game_time_start,
            "game_time_end": chronicle.game_time_end,
            "formatted_start": _format_game_time(chronicle.game_time_start),
            "formatted_end": _format_game_time(chronicle.game_time_end) if chronicle.game_time_end else None,
            "significance": chronicle.significance,
            "consequences": chronicle.consequences,
            "tags": chronicle.tags,
        },
        "events": events,
        "event_count": len(events),
    }
    
    return [TextContent(type="text", text=json.dumps(result))]
