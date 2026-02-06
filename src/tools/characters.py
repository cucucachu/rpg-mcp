"""Character tools: create, delete, rename, move, set_level, set_attribute, set_skill, 
grant_ability, revoke_ability, apply_status, remove_status, join_faction, leave_faction, set_faction_standing."""

from typing import Any
from bson import ObjectId
from mcp.types import Tool, TextContent

from ..db import database
from ..models import Character
from ..models.character import Attribute, Skill, CharacterAbility, Status, FactionMembership


def get_tools() -> tuple[list[Tool], dict[str, callable]]:
    """Return tools and handlers for character management."""
    tools = [
        Tool(
                name="create_character",
                description="Create a new character (PC or NPC)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "name": {"type": "string", "description": "Character name"},
                        "description": {"type": "string", "description": "Character description/backstory"},
                        "is_player_character": {"type": "boolean", "description": "Is this a PC?", "default": False},
                        "location_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["world_id", "name"],
                },
            ),
            Tool(
                name="delete_character",
                description="Remove a character from the game",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                    },
                    "required": ["character_id"],
                },
            ),
            Tool(
                name="rename_character",
                description="Update a character's name or description",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "name": {"type": "string", "description": "New name"},
                        "description": {"type": "string", "description": "New description"},
                    },
                    "required": ["character_id"],
                },
            ),
            Tool(
                name="move_character",
                description="Move a character to a different location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "location_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["character_id", "location_id"],
                },
            ),
            Tool(
                name="set_level",
                description="Set a character's level",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "level": {"type": "integer", "description": "New level"},
                    },
                    "required": ["character_id", "level"],
                },
            ),
            Tool(
                name="set_attributes",
                description="Set multiple character attributes at once (HP, MP, Strength, Dexterity, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "attributes": {
                            "type": "array",
                            "description": "Array of attributes to set",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Attribute name"},
                                    "value": {"description": "Attribute value"},
                                    "max": {"description": "Maximum value (optional)"},
                                },
                                "required": ["name", "value"],
                            },
                        },
                    },
                    "required": ["character_id", "attributes"],
                },
            ),
            Tool(
                name="set_skills",
                description="Set multiple character skills/proficiencies at once",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "skills": {
                            "type": "array",
                            "description": "Array of skills to set",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Skill name"},
                                    "value": {"description": "Skill value/modifier"},
                                },
                                "required": ["name", "value"],
                            },
                        },
                    },
                    "required": ["character_id", "skills"],
                },
            ),
            Tool(
                name="grant_abilities",
                description="Give a character multiple abilities at once",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "abilities": {
                            "type": "array",
                            "description": "Array of abilities to grant",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "template_id": {"type": "string", "description": "24-char hex string ID (optional)"},
                                    "name": {"type": "string", "description": "Ability name"},
                                    "description": {"type": "string", "description": "Ability description"},
                                    "attributes": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "value": {},
                                            },
                                        },
                                    },
                                },
                                "required": ["name"],
                            },
                        },
                    },
                    "required": ["character_id", "abilities"],
                },
            ),
            Tool(
                name="revoke_ability",
                description="Remove an ability from a character",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "ability_name": {"type": "string", "description": "Ability name to remove"},
                    },
                    "required": ["character_id", "ability_name"],
                },
            ),
            Tool(
                name="apply_statuses",
                description="Apply multiple status effects to a character at once",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "statuses": {
                            "type": "array",
                            "description": "Array of statuses to apply",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Status name"},
                                    "description": {"type": "string", "description": "Status description"},
                                },
                                "required": ["name"],
                            },
                        },
                    },
                    "required": ["character_id", "statuses"],
                },
            ),
            Tool(
                name="remove_status",
                description="Remove a status effect from a character",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "name": {"type": "string", "description": "Status name to remove"},
                    },
                    "required": ["character_id", "name"],
                },
            ),
            Tool(
                name="join_faction",
                description="Add a character to a faction",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "faction_id": {"type": "string", "description": "24-char hex string ID"},
                        "rank": {"type": "string", "description": "Rank in faction"},
                        "reputation": {"type": "integer", "description": "Starting reputation"},
                    },
                    "required": ["character_id", "faction_id"],
                },
            ),
            Tool(
                name="leave_faction",
                description="Remove a character from a faction",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "faction_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["character_id", "faction_id"],
                },
            ),
            Tool(
                name="set_faction_standing",
                description="Update a character's standing in a faction",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "faction_id": {"type": "string", "description": "24-char hex string ID"},
                        "rank": {"type": "string", "description": "New rank"},
                        "reputation": {"type": "integer", "description": "New reputation"},
                    },
                    "required": ["character_id", "faction_id"],
                },
            ),
            Tool(
                name="deal_damage",
                description="Deal damage to a character. Reduces HP, auto-records event, and handles 0 HP (applies 'Unconscious' status).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "amount": {"type": "integer", "description": "Damage amount"},
                        "damage_type": {"type": "string", "description": "Type of damage (e.g., slashing, fire, psychic)", "default": "untyped"},
                        "source": {"type": "string", "description": "What caused the damage (e.g., 'Goblin attack', 'Fall')"},
                        "log_event": {"type": "boolean", "description": "Whether to auto-record as event", "default": True},
                    },
                    "required": ["character_id", "amount"],
                },
            ),
            Tool(
                name="heal",
                description="Heal a character. Restores HP (up to max), auto-records event, and removes 'Unconscious' status if HP > 0.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "character_id": {"type": "string", "description": "24-char hex string ID (from create_character or load_session), NOT a name"},
                        "amount": {"type": "integer", "description": "Healing amount"},
                        "source": {"type": "string", "description": "What caused the healing (e.g., 'Healing Potion', 'Cure Wounds')"},
                        "log_event": {"type": "boolean", "description": "Whether to auto-record as event", "default": True},
                    },
                    "required": ["character_id", "amount"],
                },
            ),
            Tool(
                name="spawn_enemies",
                description="Spawn multiple NPCs quickly for an encounter. Creates characters with stats in one call.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "location_id": {"type": "string", "description": "24-char hex string ID"},
                        "enemies": {
                            "type": "array",
                            "description": "Array of enemies to spawn",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Enemy name (numbers auto-appended if count > 1)"},
                                    "count": {"type": "integer", "description": "How many to spawn", "default": 1},
                                    "description": {"type": "string"},
                                    "hp": {"type": "integer", "description": "HP (also sets max_hp)"},
                                    "level": {"type": "integer", "default": 1},
                                    "attributes": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "value": {"type": "integer"},
                                            },
                                        },
                                    },
                                    "tags": {"type": "array", "items": {"type": "string"}},
                                },
                                "required": ["name"],
                            },
                        },
                        "add_to_encounter": {"type": "string", "description": "Encounter ID to add spawned enemies to"},
                    },
                    "required": ["world_id", "enemies"],
                },
            ),
    ]
    
    handlers = {
        "create_character": _create_character,
        "delete_character": _delete_character,
        "rename_character": _rename_character,
        "move_character": _move_character,
        "set_level": _set_level,
        "set_attributes": _set_attributes,
        "set_skills": _set_skills,
        "grant_abilities": _grant_abilities,
        "revoke_ability": _revoke_ability,
        "apply_statuses": _apply_statuses,
        "remove_status": _remove_status,
        "join_faction": _join_faction,
        "leave_faction": _leave_faction,
        "set_faction_standing": _set_faction_standing,
        "deal_damage": _deal_damage,
        "heal": _heal,
        "spawn_enemies": _spawn_enemies,
    }
    
    return tools, handlers


async def _create_character(args: dict[str, Any]) -> list[TextContent]:
    """Create a new character."""
    db = database.db
    
    character = Character(
        world_id=args["world_id"],
        name=args["name"],
        description=args.get("description", ""),
        is_player_character=args.get("is_player_character", False),
        location_id=args.get("location_id"),
    )
    
    result = await db.characters.insert_one(character.to_doc())
    character.id = str(result.inserted_id)
    
    return [TextContent(type="text", text=f"Created character: {character.model_dump_json()}")]


async def _delete_character(args: dict[str, Any]) -> list[TextContent]:
    """Delete a character."""
    db = database.db
    
    result = await db.characters.delete_one({"_id": ObjectId(args["character_id"])})
    if result.deleted_count:
        return [TextContent(type="text", text=f"Deleted character {args['character_id']}")]
    return [TextContent(type="text", text=f"Character {args['character_id']} not found")]


async def _rename_character(args: dict[str, Any]) -> list[TextContent]:
    """Rename a character."""
    db = database.db
    
    update_data = {}
    if "name" in args:
        update_data["name"] = args["name"]
    if "description" in args:
        update_data["description"] = args["description"]
    
    if update_data:
        await db.characters.update_one(
            {"_id": ObjectId(args["character_id"])},
            {"$set": update_data}
        )
    
    doc = await db.characters.find_one({"_id": ObjectId(args["character_id"])})
    if doc:
        character = Character.from_doc(doc)
        return [TextContent(type="text", text=f"Updated character: {character.model_dump_json()}")]
    return [TextContent(type="text", text=f"Character {args['character_id']} not found")]


async def _move_character(args: dict[str, Any]) -> list[TextContent]:
    """Move a character to a new location."""
    db = database.db
    
    await db.characters.update_one(
        {"_id": ObjectId(args["character_id"])},
        {"$set": {"location_id": args["location_id"]}}
    )
    
    doc = await db.characters.find_one({"_id": ObjectId(args["character_id"])})
    if doc:
        character = Character.from_doc(doc)
        return [TextContent(type="text", text=f"Moved character: {character.model_dump_json()}")]
    return [TextContent(type="text", text=f"Character {args['character_id']} not found")]


async def _set_level(args: dict[str, Any]) -> list[TextContent]:
    """Set character level."""
    db = database.db
    
    await db.characters.update_one(
        {"_id": ObjectId(args["character_id"])},
        {"$set": {"level": args["level"]}}
    )
    
    doc = await db.characters.find_one({"_id": ObjectId(args["character_id"])})
    if doc:
        character = Character.from_doc(doc)
        return [TextContent(type="text", text=f"Set level: {character.model_dump_json()}")]
    return [TextContent(type="text", text=f"Character {args['character_id']} not found")]


async def _set_attributes(args: dict[str, Any]) -> list[TextContent]:
    """Set or update multiple character attributes at once."""
    db = database.db
    
    character_id = ObjectId(args["character_id"])
    attributes_to_set = args.get("attributes", [])
    
    # Get current character
    doc = await db.characters.find_one({"_id": character_id})
    if not doc:
        return [TextContent(type="text", text=f"Character {args['character_id']} not found")]
    
    character = Character.from_doc(doc)
    
    # Process each attribute
    updated_names = []
    for attr_def in attributes_to_set:
        attr_name = attr_def["name"]
        updated_names.append(attr_name)
        
        # Find or create attribute
        found = False
        for attr in character.attributes:
            if attr.name == attr_name:
                attr.value = attr_def["value"]
                if "max" in attr_def:
                    attr.max = attr_def["max"]
                found = True
                break
        
        if not found:
            character.attributes.append(Attribute(
                name=attr_name,
                value=attr_def["value"],
                max=attr_def.get("max"),
            ))
    
    # Save
    await db.characters.update_one(
        {"_id": character_id},
        {"$set": {"attributes": [a.model_dump() for a in character.attributes]}}
    )
    
    return [TextContent(type="text", text=f"Set {len(updated_names)} attributes ({', '.join(updated_names)}): {character.model_dump_json()}")]


async def _set_skills(args: dict[str, Any]) -> list[TextContent]:
    """Set or update multiple character skills at once."""
    db = database.db
    
    character_id = ObjectId(args["character_id"])
    skills_to_set = args.get("skills", [])
    
    # Get current character
    doc = await db.characters.find_one({"_id": character_id})
    if not doc:
        return [TextContent(type="text", text=f"Character {args['character_id']} not found")]
    
    character = Character.from_doc(doc)
    
    # Process each skill
    updated_names = []
    for skill_def in skills_to_set:
        skill_name = skill_def["name"]
        updated_names.append(skill_name)
        
        # Find or create skill
        found = False
        for skill in character.skills:
            if skill.name == skill_name:
                skill.value = skill_def["value"]
                found = True
                break
        
        if not found:
            character.skills.append(Skill(name=skill_name, value=skill_def["value"]))
    
    # Save
    await db.characters.update_one(
        {"_id": character_id},
        {"$set": {"skills": [s.model_dump() for s in character.skills]}}
    )
    
    return [TextContent(type="text", text=f"Set {len(updated_names)} skills ({', '.join(updated_names)}): {character.model_dump_json()}")]


async def _grant_abilities(args: dict[str, Any]) -> list[TextContent]:
    """Grant multiple abilities to a character at once."""
    db = database.db
    
    character_id = ObjectId(args["character_id"])
    abilities_to_grant = args.get("abilities", [])
    
    # Get current character
    doc = await db.characters.find_one({"_id": character_id})
    if not doc:
        return [TextContent(type="text", text=f"Character {args['character_id']} not found")]
    
    character = Character.from_doc(doc)
    
    granted_names = []
    for ability_def in abilities_to_grant:
        # Parse attributes if provided
        attributes = [Attribute(**a) for a in ability_def.get("attributes", [])]
        
        # Create ability
        ability = CharacterAbility(
            template_id=ability_def.get("template_id"),
            name=ability_def.get("name", ""),
            description=ability_def.get("description", ""),
            attributes=attributes,
        )
        
        # If template_id provided, get name from template
        if ability.template_id and not ability.name:
            template_doc = await db.ability_templates.find_one({"_id": ObjectId(ability.template_id)})
            if template_doc:
                ability.name = template_doc.get("name", "")
                if not ability.description:
                    ability.description = template_doc.get("description", "")
        
        character.abilities.append(ability)
        granted_names.append(ability.name)
    
    # Save
    await db.characters.update_one(
        {"_id": character_id},
        {"$set": {"abilities": [a.model_dump() for a in character.abilities]}}
    )
    
    return [TextContent(type="text", text=f"Granted {len(granted_names)} abilities ({', '.join(granted_names)}): {character.model_dump_json()}")]


async def _revoke_ability(args: dict[str, Any]) -> list[TextContent]:
    """Remove an ability from a character."""
    db = database.db
    
    character_id = ObjectId(args["character_id"])
    ability_name = args["ability_name"]
    
    # Get current character
    doc = await db.characters.find_one({"_id": character_id})
    if not doc:
        return [TextContent(type="text", text=f"Character {args['character_id']} not found")]
    
    character = Character.from_doc(doc)
    
    # Remove ability
    character.abilities = [a for a in character.abilities if a.name != ability_name]
    
    # Save
    await db.characters.update_one(
        {"_id": character_id},
        {"$set": {"abilities": [a.model_dump() for a in character.abilities]}}
    )
    
    return [TextContent(type="text", text=f"Revoked ability: {character.model_dump_json()}")]


async def _apply_statuses(args: dict[str, Any]) -> list[TextContent]:
    """Apply multiple status effects to a character at once."""
    db = database.db
    
    character_id = ObjectId(args["character_id"])
    statuses_to_apply = args.get("statuses", [])
    
    # Get current character
    doc = await db.characters.find_one({"_id": character_id})
    if not doc:
        return [TextContent(type="text", text=f"Character {args['character_id']} not found")]
    
    character = Character.from_doc(doc)
    
    applied_names = []
    for status_def in statuses_to_apply:
        status_name = status_def["name"]
        applied_names.append(status_name)
        
        # Remove existing status with same name, then add new one
        character.statuses = [s for s in character.statuses if s.name != status_name]
        character.statuses.append(Status(name=status_name, description=status_def.get("description", "")))
    
    # Save
    await db.characters.update_one(
        {"_id": character_id},
        {"$set": {"statuses": [s.model_dump() for s in character.statuses]}}
    )
    
    return [TextContent(type="text", text=f"Applied {len(applied_names)} statuses ({', '.join(applied_names)}): {character.model_dump_json()}")]


async def _remove_status(args: dict[str, Any]) -> list[TextContent]:
    """Remove a status effect from a character."""
    db = database.db
    
    character_id = ObjectId(args["character_id"])
    
    # Get current character
    doc = await db.characters.find_one({"_id": character_id})
    if not doc:
        return [TextContent(type="text", text=f"Character {args['character_id']} not found")]
    
    character = Character.from_doc(doc)
    
    # Remove status
    character.statuses = [s for s in character.statuses if s.name != args["name"]]
    
    # Save
    await db.characters.update_one(
        {"_id": character_id},
        {"$set": {"statuses": [s.model_dump() for s in character.statuses]}}
    )
    
    return [TextContent(type="text", text=f"Removed status: {character.model_dump_json()}")]


async def _join_faction(args: dict[str, Any]) -> list[TextContent]:
    """Add a character to a faction."""
    db = database.db
    
    character_id = ObjectId(args["character_id"])
    
    # Get current character
    doc = await db.characters.find_one({"_id": character_id})
    if not doc:
        return [TextContent(type="text", text=f"Character {args['character_id']} not found")]
    
    character = Character.from_doc(doc)
    
    # Remove existing membership if any
    character.factions = [f for f in character.factions if f.faction_id != args["faction_id"]]
    
    # Add membership
    character.factions.append(FactionMembership(
        faction_id=args["faction_id"],
        rank=args.get("rank", ""),
        reputation=args.get("reputation", 0),
    ))
    
    # Save
    await db.characters.update_one(
        {"_id": character_id},
        {"$set": {"factions": [f.model_dump() for f in character.factions]}}
    )
    
    return [TextContent(type="text", text=f"Joined faction: {character.model_dump_json()}")]


async def _leave_faction(args: dict[str, Any]) -> list[TextContent]:
    """Remove a character from a faction."""
    db = database.db
    
    character_id = ObjectId(args["character_id"])
    
    # Get current character
    doc = await db.characters.find_one({"_id": character_id})
    if not doc:
        return [TextContent(type="text", text=f"Character {args['character_id']} not found")]
    
    character = Character.from_doc(doc)
    
    # Remove membership
    character.factions = [f for f in character.factions if f.faction_id != args["faction_id"]]
    
    # Save
    await db.characters.update_one(
        {"_id": character_id},
        {"$set": {"factions": [f.model_dump() for f in character.factions]}}
    )
    
    return [TextContent(type="text", text=f"Left faction: {character.model_dump_json()}")]


async def _set_faction_standing(args: dict[str, Any]) -> list[TextContent]:
    """Update a character's standing in a faction."""
    db = database.db
    
    character_id = ObjectId(args["character_id"])
    
    # Get current character
    doc = await db.characters.find_one({"_id": character_id})
    if not doc:
        return [TextContent(type="text", text=f"Character {args['character_id']} not found")]
    
    character = Character.from_doc(doc)
    
    # Find and update membership
    found = False
    for faction in character.factions:
        if faction.faction_id == args["faction_id"]:
            if "rank" in args:
                faction.rank = args["rank"]
            if "reputation" in args:
                faction.reputation = args["reputation"]
            found = True
            break
    
    if not found:
        return [TextContent(type="text", text=f"Character not in faction {args['faction_id']}")]
    
    # Save
    await db.characters.update_one(
        {"_id": character_id},
        {"$set": {"factions": [f.model_dump() for f in character.factions]}}
    )
    
    return [TextContent(type="text", text=f"Updated faction standing: {character.model_dump_json()}")]


async def _deal_damage(args: dict[str, Any]) -> list[TextContent]:
    """Deal damage to a character."""
    db = database.db
    
    character_id = ObjectId(args["character_id"])
    amount = args["amount"]
    damage_type = args.get("damage_type", "untyped")
    source = args.get("source", "unknown")
    log_event = args.get("log_event", True)
    
    # Get current character
    doc = await db.characters.find_one({"_id": character_id})
    if not doc:
        return [TextContent(type="text", text=f"Character {args['character_id']} not found")]
    
    character = Character.from_doc(doc)
    
    # Find HP attribute
    hp_attr = None
    for attr in character.attributes:
        if attr.name.upper() == "HP":
            hp_attr = attr
            break
    
    if not hp_attr:
        return [TextContent(type="text", text=f"Character has no HP attribute")]
    
    old_hp = hp_attr.value
    new_hp = max(0, hp_attr.value - amount)
    hp_attr.value = new_hp
    
    # Check for unconscious at 0 HP
    fell_unconscious = False
    if new_hp == 0 and old_hp > 0:
        fell_unconscious = True
        # Add unconscious status if not already present
        has_unconscious = any(s.name.lower() == "unconscious" for s in character.statuses)
        if not has_unconscious:
            character.statuses.append(Status(name="Unconscious", description="Knocked out at 0 HP"))
    
    # Save character
    await db.characters.update_one(
        {"_id": character_id},
        {"$set": {
            "attributes": [a.model_dump() for a in character.attributes],
            "statuses": [s.model_dump() for s in character.statuses],
        }}
    )
    
    # Log event
    event_id = None
    if log_event:
        # Get world's current game time
        world_doc = await db.worlds.find_one({"_id": ObjectId(character.world_id)})
        game_time = world_doc.get("game_time", 0) if world_doc else 0
        
        event_desc = f"{character.name} took {amount} {damage_type} damage from {source}. HP: {old_hp} → {new_hp}."
        if fell_unconscious:
            event_desc += " Fell unconscious!"
        
        event_doc = {
            "world_id": character.world_id,
            "game_time": game_time,
            "name": f"Damage: {character.name}",
            "description": event_desc,
            "participants": character.name,
            "location_id": character.location_id,
            "tags": ["combat", "damage"],
        }
        result = await db.events.insert_one(event_doc)
        event_id = str(result.inserted_id)
    
    import json
    output = {
        "character_id": str(character_id),
        "character_name": character.name,
        "damage": amount,
        "damage_type": damage_type,
        "source": source,
        "hp_before": old_hp,
        "hp_after": new_hp,
        "hp_max": hp_attr.max,
        "fell_unconscious": fell_unconscious,
    }
    if event_id:
        output["event_id"] = event_id
    
    return [TextContent(type="text", text=json.dumps(output))]


async def _heal(args: dict[str, Any]) -> list[TextContent]:
    """Heal a character."""
    db = database.db
    
    character_id = ObjectId(args["character_id"])
    amount = args["amount"]
    source = args.get("source", "unknown")
    log_event = args.get("log_event", True)
    
    # Get current character
    doc = await db.characters.find_one({"_id": character_id})
    if not doc:
        return [TextContent(type="text", text=f"Character {args['character_id']} not found")]
    
    character = Character.from_doc(doc)
    
    # Find HP attribute
    hp_attr = None
    for attr in character.attributes:
        if attr.name.upper() == "HP":
            hp_attr = attr
            break
    
    if not hp_attr:
        return [TextContent(type="text", text=f"Character has no HP attribute")]
    
    old_hp = hp_attr.value
    max_hp = hp_attr.max if hp_attr.max else 999999
    new_hp = min(max_hp, hp_attr.value + amount)
    actual_healing = new_hp - old_hp
    hp_attr.value = new_hp
    
    # Remove unconscious status if HP > 0
    regained_consciousness = False
    if new_hp > 0 and old_hp == 0:
        old_status_count = len(character.statuses)
        character.statuses = [s for s in character.statuses if s.name.lower() != "unconscious"]
        if len(character.statuses) < old_status_count:
            regained_consciousness = True
    
    # Save character
    await db.characters.update_one(
        {"_id": character_id},
        {"$set": {
            "attributes": [a.model_dump() for a in character.attributes],
            "statuses": [s.model_dump() for s in character.statuses],
        }}
    )
    
    # Log event
    event_id = None
    if log_event and actual_healing > 0:
        # Get world's current game time
        world_doc = await db.worlds.find_one({"_id": ObjectId(character.world_id)})
        game_time = world_doc.get("game_time", 0) if world_doc else 0
        
        event_desc = f"{character.name} healed {actual_healing} HP from {source}. HP: {old_hp} → {new_hp}."
        if regained_consciousness:
            event_desc += " Regained consciousness!"
        
        event_doc = {
            "world_id": character.world_id,
            "game_time": game_time,
            "name": f"Healing: {character.name}",
            "description": event_desc,
            "participants": character.name,
            "location_id": character.location_id,
            "tags": ["healing"],
        }
        result = await db.events.insert_one(event_doc)
        event_id = str(result.inserted_id)
    
    import json
    output = {
        "character_id": str(character_id),
        "character_name": character.name,
        "healing_requested": amount,
        "healing_actual": actual_healing,
        "source": source,
        "hp_before": old_hp,
        "hp_after": new_hp,
        "hp_max": hp_attr.max,
        "regained_consciousness": regained_consciousness,
    }
    if event_id:
        output["event_id"] = event_id
    
    return [TextContent(type="text", text=json.dumps(output))]


async def _spawn_enemies(args: dict[str, Any]) -> list[TextContent]:
    """Spawn multiple NPCs for an encounter."""
    import json
    db = database.db
    
    world_id = args["world_id"]
    location_id = args.get("location_id")
    enemies = args.get("enemies", [])
    add_to_encounter = args.get("add_to_encounter")
    
    spawned = []
    
    for enemy_def in enemies:
        name_base = enemy_def["name"]
        count = enemy_def.get("count", 1)
        description = enemy_def.get("description", "")
        hp = enemy_def.get("hp")
        level = enemy_def.get("level", 1)
        attributes_def = enemy_def.get("attributes", [])
        tags = enemy_def.get("tags", [])
        
        for i in range(count):
            # Add number suffix if multiple
            name = f"{name_base} {i + 1}" if count > 1 else name_base
            
            # Build attributes list
            attributes = []
            for attr in attributes_def:
                attributes.append(Attribute(
                    name=attr["name"],
                    value=attr.get("value", 10),
                    max=attr.get("max"),
                ))
            
            # Add HP as attribute if specified
            if hp is not None:
                attributes.append(Attribute(name="HP", value=hp, max=hp))
            
            character = Character(
                world_id=world_id,
                name=name,
                description=description,
                is_player_character=False,
                location_id=location_id,
                level=level,
                hp=hp if hp else 10,
                max_hp=hp if hp else 10,
                attributes=attributes,
                tags=tags,
            )
            
            result = await db.characters.insert_one(character.to_doc())
            character.id = str(result.inserted_id)
            
            spawned.append({
                "id": character.id,
                "name": name,
                "hp": hp,
                "level": level,
            })
    
    # Add to encounter if specified
    if add_to_encounter:
        from ..models.encounter import Combatant
        combatants = [Combatant(character_id=s["id"]).model_dump() for s in spawned]
        await db.encounters.update_one(
            {"_id": ObjectId(add_to_encounter)},
            {"$push": {"combatants": {"$each": combatants}}}
        )
    
    output = {
        "spawned": spawned,
        "total": len(spawned),
        "location_id": location_id,
    }
    if add_to_encounter:
        output["added_to_encounter"] = add_to_encounter
    
    return [TextContent(type="text", text=json.dumps(output))]
