"""Group tools: form_party, disband_party, rename_party, add_to_party, remove_from_party, set_party_leader."""

from typing import Any
from bson import ObjectId
from mcp.types import Tool, TextContent

from ..db import database
from ..models import Party


def get_tools() -> tuple[list[Tool], dict[str, callable]]:
    """Return tools and handlers for group management."""
    tools = [
            Tool(
                name="form_party",
                description="Create a new party (adventuring group)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "name": {"type": "string", "description": "Party name"},
                        "description": {"type": "string", "description": "Party description"},
                        "leader_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                        "members": {"type": "array", "items": {"type": "string"}, "description": "Character IDs of members"},
                        "formed_at": {"type": "integer", "description": "Game time when formed"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["world_id", "formed_at"],
                },
            ),
            Tool(
                name="disband_party",
                description="Dissolve a party",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "party_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["party_id"],
                },
            ),
            Tool(
                name="rename_party",
                description="Update party name or description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "party_id": {"type": "string", "description": "24-char hex string ID"},
                        "name": {"type": "string", "description": "New name"},
                        "description": {"type": "string", "description": "New description"},
                    },
                    "required": ["party_id"],
                },
            ),
            Tool(
                name="add_to_party",
                description="Add a character to a party",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "party_id": {"type": "string", "description": "24-char hex string ID"},
                        "character_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                    },
                    "required": ["party_id", "character_id"],
                },
            ),
            Tool(
                name="remove_from_party",
                description="Remove a character from a party",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "party_id": {"type": "string", "description": "24-char hex string ID"},
                        "character_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                    },
                    "required": ["party_id", "character_id"],
                },
            ),
            Tool(
                name="set_party_leader",
                description="Set the party leader",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "party_id": {"type": "string", "description": "24-char hex string ID"},
                        "character_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                    },
                    "required": ["party_id", "character_id"],
                },
            ),
    ]
    
    handlers = {
        "form_party": _form_party,
        "disband_party": _disband_party,
        "rename_party": _rename_party,
        "add_to_party": _add_to_party,
        "remove_from_party": _remove_from_party,
        "set_party_leader": _set_party_leader,
    }
    
    return tools, handlers


async def _form_party(args: dict[str, Any]) -> list[TextContent]:
    """Create a new party."""
    db = database.db
    
    party = Party(
        world_id=args["world_id"],
        name=args.get("name", ""),
        description=args.get("description", ""),
        members=args.get("members", []),
        leader_id=args.get("leader_id"),
        formed_at=args["formed_at"],
        tags=args.get("tags", []),
    )
    
    result = await db.parties.insert_one(party.to_doc())
    party.id = str(result.inserted_id)
    
    return [TextContent(type="text", text=f"Formed party: {party.model_dump_json()}")]


async def _disband_party(args: dict[str, Any]) -> list[TextContent]:
    """Dissolve a party."""
    db = database.db
    
    result = await db.parties.delete_one({"_id": ObjectId(args["party_id"])})
    if result.deleted_count:
        return [TextContent(type="text", text=f"Disbanded party {args['party_id']}")]
    return [TextContent(type="text", text=f"Party {args['party_id']} not found")]


async def _rename_party(args: dict[str, Any]) -> list[TextContent]:
    """Rename a party."""
    db = database.db
    
    party_id = ObjectId(args["party_id"])
    
    update_data = {}
    if "name" in args:
        update_data["name"] = args["name"]
    if "description" in args:
        update_data["description"] = args["description"]
    
    if update_data:
        await db.parties.update_one({"_id": party_id}, {"$set": update_data})
    
    doc = await db.parties.find_one({"_id": party_id})
    if doc:
        party = Party.from_doc(doc)
        return [TextContent(type="text", text=f"Renamed party: {party.model_dump_json()}")]
    return [TextContent(type="text", text=f"Party {args['party_id']} not found")]


async def _add_to_party(args: dict[str, Any]) -> list[TextContent]:
    """Add a character to a party."""
    db = database.db
    
    party_id = ObjectId(args["party_id"])
    
    await db.parties.update_one(
        {"_id": party_id},
        {"$addToSet": {"members": args["character_id"]}}
    )
    
    doc = await db.parties.find_one({"_id": party_id})
    if doc:
        party = Party.from_doc(doc)
        return [TextContent(type="text", text=f"Added to party: {party.model_dump_json()}")]
    return [TextContent(type="text", text=f"Party {args['party_id']} not found")]


async def _remove_from_party(args: dict[str, Any]) -> list[TextContent]:
    """Remove a character from a party."""
    db = database.db
    
    party_id = ObjectId(args["party_id"])
    
    await db.parties.update_one(
        {"_id": party_id},
        {"$pull": {"members": args["character_id"]}}
    )
    
    doc = await db.parties.find_one({"_id": party_id})
    if doc:
        party = Party.from_doc(doc)
        return [TextContent(type="text", text=f"Removed from party: {party.model_dump_json()}")]
    return [TextContent(type="text", text=f"Party {args['party_id']} not found")]


async def _set_party_leader(args: dict[str, Any]) -> list[TextContent]:
    """Set the party leader."""
    db = database.db
    
    party_id = ObjectId(args["party_id"])
    
    await db.parties.update_one(
        {"_id": party_id},
        {"$set": {"leader_id": args["character_id"]}}
    )
    
    doc = await db.parties.find_one({"_id": party_id})
    if doc:
        party = Party.from_doc(doc)
        return [TextContent(type="text", text=f"Set party leader: {party.model_dump_json()}")]
    return [TextContent(type="text", text=f"Party {args['party_id']} not found")]
