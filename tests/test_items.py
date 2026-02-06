"""Tests for item tools."""

import pytest
from bson import ObjectId

from src.tools.items import (
    _spawn_item,
    _destroy_item,
    _give_item,
    _drop_item,
    _set_item_quantity,
    _set_item_attribute,
    _apply_item_status,
    _remove_item_status,
)


@pytest.mark.asyncio
async def test_spawn_item_custom(db, world_id, character_id):
    """Test spawning a custom item."""
    result = await _spawn_item({
        "world_id": world_id,
        "name": "Magic Ring",
        "description": "A ring of power",
        "owner_id": character_id,
        "attributes": [{"name": "magic", "value": 5}],
        "tags": ["ring", "magic"],
    })
    
    assert len(result) == 1
    assert "Spawned item" in result[0].text
    assert "Magic Ring" in result[0].text
    
    # Verify in database
    items = await db.items.find().to_list(100)
    assert len(items) == 1
    assert items[0]["name"] == "Magic Ring"
    assert items[0]["owner_id"] == character_id


@pytest.mark.asyncio
async def test_spawn_item_from_template(db, world_id, character_id):
    """Test spawning an item from a template."""
    # Create template
    template = await db.item_templates.insert_one({
        "world_id": world_id,
        "name": "Iron Sword",
        "description": "A sturdy sword",
        "stackable": False,
        "attributes": [{"name": "damage", "value": "1d8"}],
    })
    template_id = str(template.inserted_id)
    
    result = await _spawn_item({
        "world_id": world_id,
        "template_id": template_id,
        "owner_id": character_id,
    })
    
    assert len(result) == 1
    assert "Spawned item" in result[0].text
    assert "Iron Sword" in result[0].text
    
    # Verify item inherited template values
    item = await db.items.find_one({})
    assert item["name"] == "Iron Sword"
    assert item["template_id"] == template_id


@pytest.mark.asyncio
async def test_destroy_item(db, world_id, character_id):
    """Test destroying an item."""
    # Create an item
    item = await db.items.insert_one({
        "world_id": world_id,
        "name": "Test Item",
        "owner_id": character_id,
    })
    item_id = str(item.inserted_id)
    
    result = await _destroy_item({"item_id": item_id})
    
    assert len(result) == 1
    assert "Destroyed item" in result[0].text
    
    # Verify in database
    item = await db.items.find_one({"_id": ObjectId(item_id)})
    assert item is None


@pytest.mark.asyncio
async def test_give_item(db, world_id, character_id, location_id):
    """Test giving an item to a character."""
    # Create an item at a location
    item = await db.items.insert_one({
        "world_id": world_id,
        "name": "Found Treasure",
        "location_id": location_id,
    })
    item_id = str(item.inserted_id)
    
    # Create another character
    other_char = await db.characters.insert_one({
        "world_id": world_id,
        "name": "Other Character",
    })
    other_char_id = str(other_char.inserted_id)
    
    result = await _give_item({
        "item_id": item_id,
        "character_id": other_char_id,
    })
    
    assert len(result) == 1
    assert "Gave item" in result[0].text
    
    # Verify item is now owned and not at location
    item = await db.items.find_one({"_id": ObjectId(item_id)})
    assert item["owner_id"] == other_char_id
    assert item["location_id"] is None


@pytest.mark.asyncio
async def test_drop_item(db, world_id, character_id, location_id):
    """Test dropping an item at a location."""
    # Create an item owned by character
    item = await db.items.insert_one({
        "world_id": world_id,
        "name": "Dropped Item",
        "owner_id": character_id,
    })
    item_id = str(item.inserted_id)
    
    result = await _drop_item({
        "item_id": item_id,
        "location_id": location_id,
    })
    
    assert len(result) == 1
    assert "Dropped item" in result[0].text
    
    # Verify item is now at location and not owned
    item = await db.items.find_one({"_id": ObjectId(item_id)})
    assert item["location_id"] == location_id
    assert item["owner_id"] is None


@pytest.mark.asyncio
async def test_set_item_quantity(db, world_id, character_id):
    """Test setting item quantity."""
    # Create a stackable item
    item = await db.items.insert_one({
        "world_id": world_id,
        "name": "Gold Coins",
        "owner_id": character_id,
        "quantity": 100,
    })
    item_id = str(item.inserted_id)
    
    result = await _set_item_quantity({
        "item_id": item_id,
        "quantity": 150,
    })
    
    assert len(result) == 1
    assert "Set quantity" in result[0].text
    
    # Verify in database
    item = await db.items.find_one({"_id": ObjectId(item_id)})
    assert item["quantity"] == 150


@pytest.mark.asyncio
async def test_set_item_attribute(db, world_id, character_id):
    """Test setting an item attribute."""
    # Create an item
    item = await db.items.insert_one({
        "world_id": world_id,
        "name": "Sword",
        "owner_id": character_id,
        "attributes": [{"name": "damage", "value": "1d6"}],
    })
    item_id = str(item.inserted_id)
    
    result = await _set_item_attribute({
        "item_id": item_id,
        "name": "damage",
        "value": "1d8",
    })
    
    assert len(result) == 1
    assert "Set attribute" in result[0].text
    
    # Verify in database
    item = await db.items.find_one({"_id": ObjectId(item_id)})
    assert item["attributes"][0]["value"] == "1d8"


@pytest.mark.asyncio
async def test_apply_item_status(db, world_id, character_id):
    """Test applying a status to an item."""
    # Create an item
    item = await db.items.insert_one({
        "world_id": world_id,
        "name": "Sword",
        "owner_id": character_id,
        "statuses": [],
    })
    item_id = str(item.inserted_id)
    
    result = await _apply_item_status({
        "item_id": item_id,
        "name": "Enchanted",
        "description": "Glows with magical energy",
    })
    
    assert len(result) == 1
    assert "Applied status" in result[0].text
    
    # Verify in database
    item = await db.items.find_one({"_id": ObjectId(item_id)})
    assert len(item["statuses"]) == 1
    assert item["statuses"][0]["name"] == "Enchanted"


@pytest.mark.asyncio
async def test_remove_item_status(db, world_id, character_id):
    """Test removing a status from an item."""
    # Create an item with a status
    item = await db.items.insert_one({
        "world_id": world_id,
        "name": "Sword",
        "owner_id": character_id,
        "statuses": [{"name": "Damaged", "description": "Chipped blade"}],
    })
    item_id = str(item.inserted_id)
    
    result = await _remove_item_status({
        "item_id": item_id,
        "name": "Damaged",
    })
    
    assert len(result) == 1
    assert "Removed status" in result[0].text
    
    # Verify in database
    item = await db.items.find_one({"_id": ObjectId(item_id)})
    assert len(item["statuses"]) == 0
