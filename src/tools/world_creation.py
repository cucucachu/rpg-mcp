"""World Creation tools: set_world, set_lore, set_location, set_faction, set_item_blueprint, set_ability_blueprint."""

from typing import Any, Optional
from bson import ObjectId
from mcp.types import Tool, TextContent

from ..db import database
from ..models import World, Lore, Location, Faction, ItemTemplate, AbilityTemplate
from ..models.location import GeoJSONPoint, GeoJSONPolygon, Connection
from ..models.faction import FactionRelationship
from ..models.character import Attribute
from ..models.quest import RelatedEntity


def get_tools() -> tuple[list[Tool], dict[str, callable]]:
    """Return tools and handlers for world creation."""
    tools = [
            Tool(
                name="set_world",
                description="Create, update, or delete a game world",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "24-char hex string ID (omit to create new, provide to update)"},
                        "name": {"type": "string", "description": "World name"},
                        "description": {"type": "string", "description": "World description"},
                        "settings": {"type": "object", "description": "Freeform game settings and rules"},
                        "delete": {"type": "boolean", "description": "If true, delete the world", "default": False},
                    },
                    "required": [],
                },
            ),
            Tool(
                name="set_lore",
                description="Create, update, or delete a lore entry (history, legends, world-building)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "24-char hex string ID (omit to create new)"},
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "title": {"type": "string", "description": "Lore title"},
                        "content": {"type": "string", "description": "The lore text"},
                        "time_start": {"type": "string", "description": "When this period/event started (e.g., '1000 years before')"},
                        "time_end": {"type": "string", "description": "When this period/event ended"},
                        "related_entities": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "entity_type": {"type": "string"},
                                    "entity_id": {"type": "string"},
                                },
                            },
                            "description": "Related characters, locations, items",
                        },
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "delete": {"type": "boolean", "default": False},
                    },
                    "required": [],
                },
            ),
            Tool(
                name="set_location",
                description="Create, update, or delete a location (places, dungeons, rooms)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "24-char hex string ID (omit to create new)"},
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "name": {"type": "string", "description": "Location name"},
                        "description": {"type": "string", "description": "Location description"},
                        "parent_location_id": {"type": "string", "description": "24-char hex string ID (for hierarchy)"},
                        "coordinates": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "number"},
                                "y": {"type": "number"},
                            },
                            "description": "Location coordinates [x, y]",
                        },
                        "bounds": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {"type": "number"},
                            },
                            "description": "Polygon bounds [[x1,y1], [x2,y2], ...]",
                        },
                        "connections": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "location_id": {"type": "string"},
                                    "direction": {"type": "string"},
                                    "description": {"type": "string"},
                                    "tags": {"type": "array", "items": {"type": "string"}},
                                },
                            },
                            "description": "Connections to other locations",
                        },
                        "attributes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "value": {},
                                    "max": {},
                                },
                            },
                        },
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "delete": {"type": "boolean", "default": False},
                    },
                    "required": [],
                },
            ),
            Tool(
                name="set_faction",
                description="Create, update, or delete a faction (organizations, guilds, armies)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "24-char hex string ID (omit to create new)"},
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "name": {"type": "string", "description": "Faction name"},
                        "description": {"type": "string", "description": "Faction description, goals, history"},
                        "type": {"type": "string", "description": "Faction type (military, guild, government, etc.)"},
                        "headquarters_id": {"type": "string", "description": "24-char hex string ID"},
                        "leader_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                        "relationships": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "faction_id": {"type": "string"},
                                    "status": {"type": "string"},
                                    "description": {"type": "string"},
                                },
                            },
                            "description": "Relationships with other factions",
                        },
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
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "delete": {"type": "boolean", "default": False},
                    },
                    "required": [],
                },
            ),
            Tool(
                name="set_item_blueprint",
                description="Create, update, or delete an item template/blueprint",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "24-char hex string ID (omit to create new)"},
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "name": {"type": "string", "description": "Item name"},
                        "description": {"type": "string", "description": "Item description"},
                        "stackable": {"type": "boolean", "description": "Whether items can stack", "default": False},
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
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "delete": {"type": "boolean", "default": False},
                    },
                    "required": [],
                },
            ),
        Tool(
            name="set_ability_blueprint",
            description="Create, update, or delete an ability template/blueprint",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "24-char hex string ID (omit to create new)"},
                    "world_id": {"type": "string", "description": "24-char hex string ID"},
                    "name": {"type": "string", "description": "Ability name"},
                    "description": {"type": "string", "description": "Ability description"},
                    "type": {"type": "string", "description": "Ability type (spell, attack, passive, etc.)"},
                    "cost": {"type": "string", "description": "Cost to use (e.g., '10 MP', '1 action')"},
                    "effect": {"type": "string", "description": "What the ability does"},
                    "requirements": {"type": "string", "description": "Requirements to learn/use"},
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
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "delete": {"type": "boolean", "default": False},
                },
                "required": [],
            },
        ),
    ]
    
    handlers = {
        "set_world": _set_world,
        "set_lore": _set_lore,
        "set_location": _set_location,
        "set_faction": _set_faction,
        "set_item_blueprint": _set_item_blueprint,
        "set_ability_blueprint": _set_ability_blueprint,
    }
    
    return tools, handlers


async def _set_world(args: dict[str, Any]) -> list[TextContent]:
    """Create, update, or delete a world."""
    db = database.db
    
    # Delete
    if args.get("delete") and args.get("id"):
        result = await db.worlds.delete_one({"_id": ObjectId(args["id"])})
        if result.deleted_count:
            return [TextContent(type="text", text=f"Deleted world {args['id']}")]
        return [TextContent(type="text", text=f"World {args['id']} not found")]
    
    # Create or update
    world_id = args.get("id")
    
    if world_id:
        # Update existing
        update_data = {}
        if "name" in args:
            update_data["name"] = args["name"]
        if "description" in args:
            update_data["description"] = args["description"]
        if "settings" in args:
            update_data["settings"] = args["settings"]
        
        if update_data:
            await db.worlds.update_one(
                {"_id": ObjectId(world_id)},
                {"$set": update_data}
            )
        
        doc = await db.worlds.find_one({"_id": ObjectId(world_id)})
        world = World.from_doc(doc)
        return [TextContent(type="text", text=f"Updated world: {world.model_dump_json()}")]
    else:
        # Create new
        world = World(
            name=args.get("name", "New World"),
            description=args.get("description", ""),
            settings=args.get("settings", {}),
        )
        result = await db.worlds.insert_one(world.to_doc())
        world.id = str(result.inserted_id)
        return [TextContent(type="text", text=f"Created world: {world.model_dump_json()}")]


async def _set_lore(args: dict[str, Any]) -> list[TextContent]:
    """Create, update, or delete a lore entry."""
    db = database.db
    
    # Delete
    if args.get("delete") and args.get("id"):
        result = await db.lore.delete_one({"_id": ObjectId(args["id"])})
        if result.deleted_count:
            return [TextContent(type="text", text=f"Deleted lore {args['id']}")]
        return [TextContent(type="text", text=f"Lore {args['id']} not found")]
    
    lore_id = args.get("id")
    
    # Parse related entities
    related_entities = [
        RelatedEntity(**e) for e in args.get("related_entities", [])
    ]
    
    if lore_id:
        # Update existing
        update_data = {}
        for field in ["world_id", "title", "content", "time_start", "time_end", "tags"]:
            if field in args:
                update_data[field] = args[field]
        if "related_entities" in args:
            update_data["related_entities"] = [e.model_dump() for e in related_entities]
        
        if update_data:
            await db.lore.update_one(
                {"_id": ObjectId(lore_id)},
                {"$set": update_data}
            )
        
        doc = await db.lore.find_one({"_id": ObjectId(lore_id)})
        lore = Lore.from_doc(doc)
        return [TextContent(type="text", text=f"Updated lore: {lore.model_dump_json()}")]
    else:
        # Create new
        lore = Lore(
            world_id=args["world_id"],
            title=args.get("title", ""),
            content=args.get("content", ""),
            time_start=args.get("time_start", ""),
            time_end=args.get("time_end", ""),
            related_entities=related_entities,
            tags=args.get("tags", []),
        )
        result = await db.lore.insert_one(lore.to_doc())
        lore.id = str(result.inserted_id)
        return [TextContent(type="text", text=f"Created lore: {lore.model_dump_json()}")]


async def _set_location(args: dict[str, Any]) -> list[TextContent]:
    """Create, update, or delete a location."""
    db = database.db
    
    # Delete
    if args.get("delete") and args.get("id"):
        result = await db.locations.delete_one({"_id": ObjectId(args["id"])})
        if result.deleted_count:
            return [TextContent(type="text", text=f"Deleted location {args['id']}")]
        return [TextContent(type="text", text=f"Location {args['id']} not found")]
    
    location_id = args.get("id")
    
    # Parse coordinates
    coordinates = None
    if args.get("coordinates"):
        coords = args["coordinates"]
        coordinates = GeoJSONPoint(coordinates=[coords["x"], coords["y"]])
    
    # Parse bounds
    bounds = None
    if args.get("bounds"):
        bounds = GeoJSONPolygon(coordinates=[args["bounds"]])
    
    # Parse connections
    connections = [
        Connection(**c) for c in args.get("connections", [])
    ]
    
    # Parse attributes
    attributes = [
        Attribute(**a) for a in args.get("attributes", [])
    ]
    
    if location_id:
        # Update existing
        update_data = {}
        for field in ["world_id", "name", "description", "parent_location_id", "tags"]:
            if field in args:
                update_data[field] = args[field]
        if coordinates:
            update_data["coordinates"] = coordinates.model_dump()
        if bounds:
            update_data["bounds"] = bounds.model_dump()
        if "connections" in args:
            update_data["connections"] = [c.model_dump() for c in connections]
        if "attributes" in args:
            update_data["attributes"] = [a.model_dump() for a in attributes]
        
        if update_data:
            await db.locations.update_one(
                {"_id": ObjectId(location_id)},
                {"$set": update_data}
            )
        
        doc = await db.locations.find_one({"_id": ObjectId(location_id)})
        location = Location.from_doc(doc)
        return [TextContent(type="text", text=f"Updated location: {location.model_dump_json()}")]
    else:
        # Create new
        location = Location(
            world_id=args["world_id"],
            name=args.get("name", ""),
            description=args.get("description", ""),
            parent_location_id=args.get("parent_location_id"),
            coordinates=coordinates,
            bounds=bounds,
            connections=connections,
            attributes=attributes,
            tags=args.get("tags", []),
        )
        result = await db.locations.insert_one(location.to_doc())
        location.id = str(result.inserted_id)
        return [TextContent(type="text", text=f"Created location: {location.model_dump_json()}")]


async def _set_faction(args: dict[str, Any]) -> list[TextContent]:
    """Create, update, or delete a faction."""
    db = database.db
    
    # Delete
    if args.get("delete") and args.get("id"):
        result = await db.factions.delete_one({"_id": ObjectId(args["id"])})
        if result.deleted_count:
            return [TextContent(type="text", text=f"Deleted faction {args['id']}")]
        return [TextContent(type="text", text=f"Faction {args['id']} not found")]
    
    faction_id = args.get("id")
    
    # Parse relationships
    relationships = [
        FactionRelationship(**r) for r in args.get("relationships", [])
    ]
    
    # Parse attributes
    attributes = [
        Attribute(**a) for a in args.get("attributes", [])
    ]
    
    if faction_id:
        # Update existing
        update_data = {}
        for field in ["world_id", "name", "description", "type", "headquarters_id", "leader_id", "tags"]:
            if field in args:
                update_data[field] = args[field]
        if "relationships" in args:
            update_data["relationships"] = [r.model_dump() for r in relationships]
        if "attributes" in args:
            update_data["attributes"] = [a.model_dump() for a in attributes]
        
        if update_data:
            await db.factions.update_one(
                {"_id": ObjectId(faction_id)},
                {"$set": update_data}
            )
        
        doc = await db.factions.find_one({"_id": ObjectId(faction_id)})
        faction = Faction.from_doc(doc)
        return [TextContent(type="text", text=f"Updated faction: {faction.model_dump_json()}")]
    else:
        # Create new
        faction = Faction(
            world_id=args["world_id"],
            name=args.get("name", ""),
            description=args.get("description", ""),
            type=args.get("type", ""),
            headquarters_id=args.get("headquarters_id"),
            leader_id=args.get("leader_id"),
            relationships=relationships,
            attributes=attributes,
            tags=args.get("tags", []),
        )
        result = await db.factions.insert_one(faction.to_doc())
        faction.id = str(result.inserted_id)
        return [TextContent(type="text", text=f"Created faction: {faction.model_dump_json()}")]


async def _set_item_blueprint(args: dict[str, Any]) -> list[TextContent]:
    """Create, update, or delete an item template."""
    db = database.db
    
    # Delete
    if args.get("delete") and args.get("id"):
        result = await db.item_templates.delete_one({"_id": ObjectId(args["id"])})
        if result.deleted_count:
            return [TextContent(type="text", text=f"Deleted item blueprint {args['id']}")]
        return [TextContent(type="text", text=f"Item blueprint {args['id']} not found")]
    
    template_id = args.get("id")
    
    # Parse attributes
    attributes = [
        Attribute(**a) for a in args.get("attributes", [])
    ]
    
    if template_id:
        # Update existing
        update_data = {}
        for field in ["world_id", "name", "description", "stackable", "tags"]:
            if field in args:
                update_data[field] = args[field]
        if "attributes" in args:
            update_data["attributes"] = [a.model_dump() for a in attributes]
        
        if update_data:
            await db.item_templates.update_one(
                {"_id": ObjectId(template_id)},
                {"$set": update_data}
            )
        
        doc = await db.item_templates.find_one({"_id": ObjectId(template_id)})
        template = ItemTemplate.from_doc(doc)
        return [TextContent(type="text", text=f"Updated item blueprint: {template.model_dump_json()}")]
    else:
        # Create new
        template = ItemTemplate(
            world_id=args["world_id"],
            name=args.get("name", ""),
            description=args.get("description", ""),
            stackable=args.get("stackable", False),
            attributes=attributes,
            tags=args.get("tags", []),
        )
        result = await db.item_templates.insert_one(template.to_doc())
        template.id = str(result.inserted_id)
        return [TextContent(type="text", text=f"Created item blueprint: {template.model_dump_json()}")]


async def _set_ability_blueprint(args: dict[str, Any]) -> list[TextContent]:
    """Create, update, or delete an ability template."""
    db = database.db
    
    # Delete
    if args.get("delete") and args.get("id"):
        result = await db.ability_templates.delete_one({"_id": ObjectId(args["id"])})
        if result.deleted_count:
            return [TextContent(type="text", text=f"Deleted ability blueprint {args['id']}")]
        return [TextContent(type="text", text=f"Ability blueprint {args['id']} not found")]
    
    template_id = args.get("id")
    
    # Parse attributes
    attributes = [
        Attribute(**a) for a in args.get("attributes", [])
    ]
    
    if template_id:
        # Update existing
        update_data = {}
        for field in ["world_id", "name", "description", "type", "cost", "effect", "requirements", "tags"]:
            if field in args:
                update_data[field] = args[field]
        if "attributes" in args:
            update_data["attributes"] = [a.model_dump() for a in attributes]
        
        if update_data:
            await db.ability_templates.update_one(
                {"_id": ObjectId(template_id)},
                {"$set": update_data}
            )
        
        doc = await db.ability_templates.find_one({"_id": ObjectId(template_id)})
        template = AbilityTemplate.from_doc(doc)
        return [TextContent(type="text", text=f"Updated ability blueprint: {template.model_dump_json()}")]
    else:
        # Create new
        template = AbilityTemplate(
            world_id=args["world_id"],
            name=args.get("name", ""),
            description=args.get("description", ""),
            type=args.get("type", ""),
            cost=args.get("cost", ""),
            effect=args.get("effect", ""),
            requirements=args.get("requirements", ""),
            attributes=attributes,
            tags=args.get("tags", []),
        )
        result = await db.ability_templates.insert_one(template.to_doc())
        template.id = str(result.inserted_id)
        return [TextContent(type="text", text=f"Created ability blueprint: {template.model_dump_json()}")]
