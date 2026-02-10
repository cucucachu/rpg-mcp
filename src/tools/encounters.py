"""Encounter tools: manage turn-based encounters (combat, chases, etc.)."""

import json
from typing import Any
from bson import ObjectId
from mcp.types import Tool, TextContent

from ..db import database
from ..utils import get_world_game_time
from ..models import Encounter, Combatant, Character


def get_tools() -> tuple[list[Tool], dict[str, callable]]:
    """Return encounter management tools and their handlers."""
    tools = [
        Tool(
            name="start_encounter",
            description="Start a new encounter (combat, chase, social challenge). Optionally adds combatants and rolls initiative.",
            inputSchema={
                "type": "object",
                "properties": {
                    "world_id": {"type": "string", "description": "24-char hex string ID"},
                    "name": {"type": "string", "description": "Encounter name (e.g., 'Ambush at the Bridge')"},
                    "location_id": {"type": "string", "description": "24-char hex string ID"},
                    "encounter_type": {"type": "string", "description": "Type: combat, chase, social, custom", "default": "combat"},
                    "combatant_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of 24-char hex string IDs (NOT names)"
                    },
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["world_id"],
            },
        ),
        Tool(
            name="get_encounter",
            description="Get current encounter state including turn order, current combatant, round number",
            inputSchema={
                "type": "object",
                "properties": {
                    "encounter_id": {"type": "string", "description": "24-char hex string ID"},
                },
                "required": ["encounter_id"],
            },
        ),
        Tool(
            name="get_active_encounter",
            description="Get the active encounter for a world (if any)",
            inputSchema={
                "type": "object",
                "properties": {
                    "world_id": {"type": "string", "description": "24-char hex string ID"},
                },
                "required": ["world_id"],
            },
        ),
        Tool(
            name="add_combatant",
            description="Add a character to an encounter with optional initiative",
            inputSchema={
                "type": "object",
                "properties": {
                    "encounter_id": {"type": "string", "description": "24-char hex string ID"},
                    "character_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                    "initiative": {"type": "number", "description": "Initiative value (higher goes first)"},
                    "notes": {"type": "string", "description": "GM notes for this combatant"},
                },
                "required": ["encounter_id", "character_id"],
            },
        ),
        Tool(
            name="set_initiative",
            description="Set or update initiative for a combatant",
            inputSchema={
                "type": "object",
                "properties": {
                    "encounter_id": {"type": "string", "description": "24-char hex string ID"},
                    "character_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                    "initiative": {"type": "number", "description": "Initiative value"},
                },
                "required": ["encounter_id", "character_id", "initiative"],
            },
        ),
        Tool(
            name="remove_combatant",
            description="Remove a combatant from encounter (fled, captured, etc.) - does not delete character",
            inputSchema={
                "type": "object",
                "properties": {
                    "encounter_id": {"type": "string", "description": "24-char hex string ID"},
                    "character_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                    "reason": {"type": "string", "description": "Why removed (fled, surrendered, etc.)"},
                },
                "required": ["encounter_id", "character_id"],
            },
        ),
        Tool(
            name="next_turn",
            description="Advance to the next combatant's turn. Increments round when wrapping.",
            inputSchema={
                "type": "object",
                "properties": {
                    "encounter_id": {"type": "string", "description": "24-char hex string ID"},
                    "advance_time": {"type": "boolean", "description": "Advance game time by 6 seconds per round", "default": False},
                },
                "required": ["encounter_id"],
            },
        ),
        Tool(
            name="end_encounter",
            description="End an encounter with optional summary and outcome. Events are recorded by the Scribe.",
            inputSchema={
                "type": "object",
                "properties": {
                    "encounter_id": {"type": "string", "description": "24-char hex string ID"},
                    "summary": {"type": "string", "description": "Summary of what happened"},
                    "outcome": {"type": "string", "description": "victory, defeat, fled, negotiated, etc."},
                },
                "required": ["encounter_id"],
            },
        ),
    ]
    
    handlers = {
        "start_encounter": _start_encounter,
        "get_encounter": _get_encounter,
        "get_active_encounter": _get_active_encounter,
        "add_combatant": _add_combatant,
        "set_initiative": _set_initiative,
        "remove_combatant": _remove_combatant,
        "next_turn": _next_turn,
        "end_encounter": _end_encounter,
    }
    
    return tools, handlers


def _format_encounter(encounter: Encounter, characters: dict[str, Character]) -> dict:
    """Format encounter for output with character names."""
    turn_order = encounter.get_turn_order()
    current = encounter.get_current_combatant()
    
    combatants_formatted = []
    for i, c in enumerate(turn_order):
        char = characters.get(c.character_id)
        char_name = char.name if char else "Unknown"
        is_current = current and c.character_id == current.character_id
        combatants_formatted.append({
            "character_id": c.character_id,
            "name": char_name,
            "initiative": c.initiative,
            "is_current_turn": is_current,
            "is_active": c.is_active,
            "notes": c.notes,
        })
    
    current_name = None
    if current:
        char = characters.get(current.character_id)
        current_name = char.name if char else "Unknown"
    
    return {
        "id": encounter.id,
        "name": encounter.name,
        "status": encounter.status,
        "encounter_type": encounter.encounter_type,
        "location_id": encounter.location_id,
        "round": encounter.round_number,
        "current_turn": {
            "character_id": current.character_id if current else None,
            "name": current_name,
        },
        "turn_order": combatants_formatted,
        "total_combatants": len(encounter.combatants),
        "active_combatants": len(turn_order),
        "tags": encounter.tags,
    }


async def _start_encounter(args: dict[str, Any]) -> list[TextContent]:
    """Start a new encounter."""
    db = database.db
    
    world_id = args["world_id"]
    
    # Get current game time from events (not world doc)
    game_time = await get_world_game_time(db, world_id)
    
    # Create encounter
    encounter = Encounter(
        world_id=world_id,
        name=args.get("name", "Encounter"),
        location_id=args.get("location_id"),
        encounter_type=args.get("encounter_type", "combat"),
        status="active",
        started_at=game_time,
        tags=args.get("tags", []),
    )
    
    # Add initial combatants
    combatant_ids = args.get("combatant_ids", [])
    characters = {}
    for char_id in combatant_ids:
        char_doc = await db.characters.find_one({"_id": ObjectId(char_id)})
        if char_doc:
            char = Character.from_doc(char_doc)
            characters[char_id] = char
            encounter.combatants.append(Combatant(character_id=char_id))
    
    result = await db.encounters.insert_one(encounter.to_doc())
    encounter.id = str(result.inserted_id)
    
    output = _format_encounter(encounter, characters)
    output["message"] = f"Encounter '{encounter.name}' started with {len(encounter.combatants)} combatants. Set initiative for each, then use next_turn to begin."
    
    return [TextContent(type="text", text=json.dumps(output))]


async def _get_encounter(args: dict[str, Any]) -> list[TextContent]:
    """Get encounter details."""
    db = database.db
    
    encounter_id = args["encounter_id"]
    doc = await db.encounters.find_one({"_id": ObjectId(encounter_id)})
    if not doc:
        return [TextContent(type="text", text=f"Encounter {encounter_id} not found")]
    
    encounter = Encounter.from_doc(doc)
    
    # Load character names
    characters = {}
    for c in encounter.combatants:
        char_doc = await db.characters.find_one({"_id": ObjectId(c.character_id)})
        if char_doc:
            characters[c.character_id] = Character.from_doc(char_doc)
    
    return [TextContent(type="text", text=json.dumps(_format_encounter(encounter, characters)))]


async def _get_active_encounter(args: dict[str, Any]) -> list[TextContent]:
    """Get active encounter for a world."""
    db = database.db
    
    world_id = args["world_id"]
    doc = await db.encounters.find_one({"world_id": world_id, "status": "active"})
    
    if not doc:
        return [TextContent(type="text", text=json.dumps({"active": False, "message": "No active encounter"}))]
    
    encounter = Encounter.from_doc(doc)
    
    # Load character names
    characters = {}
    for c in encounter.combatants:
        char_doc = await db.characters.find_one({"_id": ObjectId(c.character_id)})
        if char_doc:
            characters[c.character_id] = Character.from_doc(char_doc)
    
    result = _format_encounter(encounter, characters)
    result["active"] = True
    return [TextContent(type="text", text=json.dumps(result))]


async def _add_combatant(args: dict[str, Any]) -> list[TextContent]:
    """Add a combatant to encounter."""
    db = database.db
    
    encounter_id = args["encounter_id"]
    character_id = args["character_id"]
    
    # Verify character exists
    char_doc = await db.characters.find_one({"_id": ObjectId(character_id)})
    if not char_doc:
        return [TextContent(type="text", text=f"Character {character_id} not found")]
    char = Character.from_doc(char_doc)
    
    # Add to encounter
    combatant = Combatant(
        character_id=character_id,
        initiative=args.get("initiative", 0),
        notes=args.get("notes", ""),
    )
    
    await db.encounters.update_one(
        {"_id": ObjectId(encounter_id)},
        {"$push": {"combatants": combatant.model_dump()}}
    )
    
    return [TextContent(type="text", text=json.dumps({
        "added": char.name,
        "character_id": character_id,
        "initiative": combatant.initiative,
    }))]


async def _set_initiative(args: dict[str, Any]) -> list[TextContent]:
    """Set initiative for a combatant."""
    db = database.db
    
    encounter_id = args["encounter_id"]
    character_id = args["character_id"]
    initiative = args["initiative"]
    
    result = await db.encounters.update_one(
        {"_id": ObjectId(encounter_id), "combatants.character_id": character_id},
        {"$set": {"combatants.$.initiative": initiative}}
    )
    
    if result.modified_count == 0:
        return [TextContent(type="text", text=f"Combatant {character_id} not found in encounter")]
    
    # Get updated encounter
    doc = await db.encounters.find_one({"_id": ObjectId(encounter_id)})
    encounter = Encounter.from_doc(doc)
    
    # Get character name
    char_doc = await db.characters.find_one({"_id": ObjectId(character_id)})
    char_name = Character.from_doc(char_doc).name if char_doc else "Unknown"
    
    # Show new turn order
    turn_order = []
    for c in encounter.get_turn_order():
        c_doc = await db.characters.find_one({"_id": ObjectId(c.character_id)})
        c_name = Character.from_doc(c_doc).name if c_doc else "Unknown"
        turn_order.append({"name": c_name, "initiative": c.initiative})
    
    return [TextContent(type="text", text=json.dumps({
        "set": char_name,
        "initiative": initiative,
        "turn_order": turn_order,
    }))]


async def _remove_combatant(args: dict[str, Any]) -> list[TextContent]:
    """Remove combatant from encounter (mark as inactive)."""
    db = database.db
    
    encounter_id = args["encounter_id"]
    character_id = args["character_id"]
    reason = args.get("reason", "")
    
    result = await db.encounters.update_one(
        {"_id": ObjectId(encounter_id), "combatants.character_id": character_id},
        {"$set": {"combatants.$.is_active": False, "combatants.$.notes": reason}}
    )
    
    if result.modified_count == 0:
        return [TextContent(type="text", text=f"Combatant {character_id} not found in encounter")]
    
    # Get character name
    char_doc = await db.characters.find_one({"_id": ObjectId(character_id)})
    char_name = Character.from_doc(char_doc).name if char_doc else "Unknown"
    
    return [TextContent(type="text", text=json.dumps({
        "removed": char_name,
        "reason": reason,
    }))]


async def _next_turn(args: dict[str, Any]) -> list[TextContent]:
    """Advance to next turn."""
    db = database.db
    
    encounter_id = args["encounter_id"]
    advance_time = args.get("advance_time", False)
    
    doc = await db.encounters.find_one({"_id": ObjectId(encounter_id)})
    if not doc:
        return [TextContent(type="text", text=f"Encounter {encounter_id} not found")]
    
    encounter = Encounter.from_doc(doc)
    
    if encounter.status != "active":
        return [TextContent(type="text", text="Encounter is not active")]
    
    turn_order = encounter.get_turn_order()
    if not turn_order:
        return [TextContent(type="text", text="No active combatants")]
    
    # Calculate new turn
    old_turn = encounter.current_turn
    new_turn = (encounter.current_turn + 1) % len(turn_order)
    new_round = encounter.round_number
    
    # Check if we wrapped around to start of turn order
    if new_turn <= old_turn or old_turn >= len(turn_order) - 1:
        if new_turn == 0:
            new_round += 1
    
    # Update encounter
    await db.encounters.update_one(
        {"_id": ObjectId(encounter_id)},
        {"$set": {"current_turn": new_turn, "round_number": new_round}}
    )
    
    # Note: advance_time deprecated - game time is now tracked via events (Scribe records combat rounds)
    
    # Get current combatant info
    current = turn_order[new_turn]
    char_doc = await db.characters.find_one({"_id": ObjectId(current.character_id)})
    char = Character.from_doc(char_doc) if char_doc else None
    
    # Load all characters for turn order display
    characters = {}
    for c in encounter.combatants:
        c_doc = await db.characters.find_one({"_id": ObjectId(c.character_id)})
        if c_doc:
            characters[c.character_id] = Character.from_doc(c_doc)
    
    # Build turn order with names
    turn_order_display = []
    for i, c in enumerate(turn_order):
        ch = characters.get(c.character_id)
        turn_order_display.append({
            "name": ch.name if ch else "Unknown",
            "initiative": c.initiative,
            "is_current": i == new_turn,
        })
    
    return [TextContent(type="text", text=json.dumps({
        "round": new_round,
        "current_turn": {
            "character_id": current.character_id,
            "name": char.name if char else "Unknown",
            "hp": f"{char.hp}/{char.max_hp}" if char else None,
            "statuses": [s.name for s in char.statuses] if char else [],
        },
        "turn_order": turn_order_display,
        "time_advanced": 0,  # Game time now tracked via events (Scribe records combat rounds)
    }))]


async def _end_encounter(args: dict[str, Any]) -> list[TextContent]:
    """End an encounter."""
    db = database.db
    
    encounter_id = args["encounter_id"]
    summary = args.get("summary", "")
    outcome = args.get("outcome", "")
    
    # Get encounter
    doc = await db.encounters.find_one({"_id": ObjectId(encounter_id)})
    if not doc:
        return [TextContent(type="text", text=f"Encounter {encounter_id} not found")]
    
    encounter = Encounter.from_doc(doc)
    
    # Derive ended_at from encounter (started_at + rounds * 6s)
    ended_at = None
    if encounter.started_at is not None:
        ended_at = encounter.started_at + (encounter.round_number * 6)
    
    # Update encounter
    update = {
        "status": "ended",
        "ended_at": ended_at,
        "summary": summary,
    }
    if outcome:
        update["metadata.outcome"] = outcome
    
    await db.encounters.update_one(
        {"_id": ObjectId(encounter_id)},
        {"$set": update}
    )
    
    return [TextContent(type="text", text=json.dumps({
        "ended": encounter.name,
        "rounds": encounter.round_number,
        "outcome": outcome,
        "summary": summary,
    }))]
