"""Item tools: spawn_item, destroy_item, give_item, drop_item, set_item_quantity, 
set_item_attribute, apply_item_status, remove_item_status."""

from typing import Any
from bson import ObjectId
from mcp.types import Tool, TextContent

from ..db import database
from ..models import Item, ItemTemplate
from ..models.item import ItemStatus
from ..models.character import Attribute


def get_tools() -> tuple[list[Tool], dict[str, callable]]:
    """Return tools and handlers for item management."""
    tools = [
            Tool(
                name="spawn_item",
                description="Create an item in the world (from template or custom)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "world_id": {"type": "string", "description": "24-char hex string ID"},
                        "template_id": {"type": "string", "description": "24-char hex string ID (optional)"},
                        "name": {"type": "string", "description": "Item name (required if no template)"},
                        "description": {"type": "string", "description": "Item description"},
                        "stackable": {"type": "boolean", "description": "Whether item stacks"},
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
                        "owner_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                        "location_id": {"type": "string", "description": "24-char hex string ID"},
                        "quantity": {"type": "integer", "description": "Quantity (for stackable items)", "default": 1},
                    },
                    "required": ["world_id"],
                },
            ),
            Tool(
                name="destroy_item",
                description="Remove an item from the game",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["item_id"],
                },
            ),
            Tool(
                name="give_item",
                description="Transfer an item to a character",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "24-char hex string ID"},
                        "character_id": {"type": "string", "description": "24-char hex string ID, NOT a name"},
                    },
                    "required": ["item_id", "character_id"],
                },
            ),
            Tool(
                name="drop_item",
                description="Place an item at a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "24-char hex string ID"},
                        "location_id": {"type": "string", "description": "24-char hex string ID"},
                    },
                    "required": ["item_id", "location_id"],
                },
            ),
            Tool(
                name="set_item_quantity",
                description="Change the quantity of a stackable item",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "24-char hex string ID"},
                        "quantity": {"type": "integer", "description": "New quantity"},
                    },
                    "required": ["item_id", "quantity"],
                },
            ),
            Tool(
                name="set_item_attribute",
                description="Set or modify an item attribute",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "24-char hex string ID"},
                        "name": {"type": "string", "description": "Attribute name"},
                        "value": {"description": "Attribute value"},
                    },
                    "required": ["item_id", "name", "value"],
                },
            ),
            Tool(
                name="apply_item_status",
                description="Apply a status/condition to an item (damaged, enchanted, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "24-char hex string ID"},
                        "name": {"type": "string", "description": "Status name"},
                        "description": {"type": "string", "description": "Status description"},
                    },
                    "required": ["item_id", "name"],
                },
            ),
            Tool(
                name="remove_item_status",
                description="Remove a status/condition from an item",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_id": {"type": "string", "description": "24-char hex string ID"},
                        "name": {"type": "string", "description": "Status name to remove"},
                    },
                    "required": ["item_id", "name"],
                },
            ),
    ]
    
    handlers = {
        "spawn_item": _spawn_item,
        "destroy_item": _destroy_item,
        "give_item": _give_item,
        "drop_item": _drop_item,
        "set_item_quantity": _set_item_quantity,
        "set_item_attribute": _set_item_attribute,
        "apply_item_status": _apply_item_status,
        "remove_item_status": _remove_item_status,
    }
    
    return tools, handlers


async def _spawn_item(args: dict[str, Any]) -> list[TextContent]:
    """Create an item in the world."""
    db = database.db
    
    # Parse attributes
    attributes = [Attribute(**a) for a in args.get("attributes", [])]
    
    # If template_id provided, get defaults from template
    name = args.get("name", "")
    description = args.get("description", "")
    
    if args.get("template_id"):
        template_doc = await db.item_templates.find_one({"_id": ObjectId(args["template_id"])})
        if template_doc:
            template = ItemTemplate.from_doc(template_doc)
            if not name:
                name = template.name
            if not description:
                description = template.description
            # Merge template attributes with provided attributes
            template_attr_names = {a.name for a in attributes}
            for ta in template.attributes:
                if ta.name not in template_attr_names:
                    attributes.append(ta)
    
    item = Item(
        world_id=args["world_id"],
        template_id=args.get("template_id"),
        name=name,
        description=description,
        owner_id=args.get("owner_id"),
        location_id=args.get("location_id"),
        quantity=args.get("quantity", 1),
        attributes=attributes,
        tags=args.get("tags", []),
    )
    
    result = await db.items.insert_one(item.to_doc())
    item.id = str(result.inserted_id)
    
    return [TextContent(type="text", text=f"Spawned item: {item.model_dump_json()}")]


async def _destroy_item(args: dict[str, Any]) -> list[TextContent]:
    """Remove an item from the game."""
    db = database.db
    
    result = await db.items.delete_one({"_id": ObjectId(args["item_id"])})
    if result.deleted_count:
        return [TextContent(type="text", text=f"Destroyed item {args['item_id']}")]
    return [TextContent(type="text", text=f"Item {args['item_id']} not found")]


async def _give_item(args: dict[str, Any]) -> list[TextContent]:
    """Transfer an item to a character."""
    db = database.db
    
    await db.items.update_one(
        {"_id": ObjectId(args["item_id"])},
        {"$set": {"owner_id": args["character_id"], "location_id": None}}
    )
    
    doc = await db.items.find_one({"_id": ObjectId(args["item_id"])})
    if doc:
        item = Item.from_doc(doc)
        return [TextContent(type="text", text=f"Gave item: {item.model_dump_json()}")]
    return [TextContent(type="text", text=f"Item {args['item_id']} not found")]


async def _drop_item(args: dict[str, Any]) -> list[TextContent]:
    """Place an item at a location."""
    db = database.db
    
    await db.items.update_one(
        {"_id": ObjectId(args["item_id"])},
        {"$set": {"location_id": args["location_id"], "owner_id": None}}
    )
    
    doc = await db.items.find_one({"_id": ObjectId(args["item_id"])})
    if doc:
        item = Item.from_doc(doc)
        return [TextContent(type="text", text=f"Dropped item: {item.model_dump_json()}")]
    return [TextContent(type="text", text=f"Item {args['item_id']} not found")]


async def _set_item_quantity(args: dict[str, Any]) -> list[TextContent]:
    """Set item quantity."""
    db = database.db
    
    await db.items.update_one(
        {"_id": ObjectId(args["item_id"])},
        {"$set": {"quantity": args["quantity"]}}
    )
    
    doc = await db.items.find_one({"_id": ObjectId(args["item_id"])})
    if doc:
        item = Item.from_doc(doc)
        return [TextContent(type="text", text=f"Set quantity: {item.model_dump_json()}")]
    return [TextContent(type="text", text=f"Item {args['item_id']} not found")]


async def _set_item_attribute(args: dict[str, Any]) -> list[TextContent]:
    """Set or update an item attribute."""
    db = database.db
    
    item_id = ObjectId(args["item_id"])
    attr_name = args["name"]
    
    doc = await db.items.find_one({"_id": item_id})
    if not doc:
        return [TextContent(type="text", text=f"Item {args['item_id']} not found")]
    
    item = Item.from_doc(doc)
    
    # Find or create attribute
    found = False
    for attr in item.attributes:
        if attr.name == attr_name:
            attr.value = args["value"]
            found = True
            break
    
    if not found:
        item.attributes.append(Attribute(name=attr_name, value=args["value"]))
    
    await db.items.update_one(
        {"_id": item_id},
        {"$set": {"attributes": [a.model_dump() for a in item.attributes]}}
    )
    
    return [TextContent(type="text", text=f"Set attribute: {item.model_dump_json()}")]


async def _apply_item_status(args: dict[str, Any]) -> list[TextContent]:
    """Apply a status to an item."""
    db = database.db
    
    item_id = ObjectId(args["item_id"])
    
    doc = await db.items.find_one({"_id": item_id})
    if not doc:
        return [TextContent(type="text", text=f"Item {args['item_id']} not found")]
    
    item = Item.from_doc(doc)
    
    # Add status (replace if exists)
    item.statuses = [s for s in item.statuses if s.name != args["name"]]
    item.statuses.append(ItemStatus(name=args["name"], description=args.get("description", "")))
    
    await db.items.update_one(
        {"_id": item_id},
        {"$set": {"statuses": [s.model_dump() for s in item.statuses]}}
    )
    
    return [TextContent(type="text", text=f"Applied status: {item.model_dump_json()}")]


async def _remove_item_status(args: dict[str, Any]) -> list[TextContent]:
    """Remove a status from an item."""
    db = database.db
    
    item_id = ObjectId(args["item_id"])
    
    doc = await db.items.find_one({"_id": item_id})
    if not doc:
        return [TextContent(type="text", text=f"Item {args['item_id']} not found")]
    
    item = Item.from_doc(doc)
    
    # Remove status
    item.statuses = [s for s in item.statuses if s.name != args["name"]]
    
    await db.items.update_one(
        {"_id": item_id},
        {"$set": {"statuses": [s.model_dump() for s in item.statuses]}}
    )
    
    return [TextContent(type="text", text=f"Removed status: {item.model_dump_json()}")]
