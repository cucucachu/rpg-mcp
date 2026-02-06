"""Tests for world creation tools."""

import pytest
from bson import ObjectId

from src.tools.world_creation import (
    _set_world,
    _set_lore,
    _set_location,
    _set_faction,
    _set_item_blueprint,
    _set_ability_blueprint,
)


@pytest.mark.asyncio
async def test_set_world_create(db):
    """Test creating a new world."""
    result = await _set_world({
        "name": "Fantasy World",
        "description": "A magical realm",
        "settings": {"magic_system": "mana"},
    })
    
    assert len(result) == 1
    assert "Created world" in result[0].text
    assert "Fantasy World" in result[0].text
    
    # Verify in database
    worlds = await db.worlds.find().to_list(100)
    assert len(worlds) == 1
    assert worlds[0]["name"] == "Fantasy World"
    assert worlds[0]["settings"]["magic_system"] == "mana"


@pytest.mark.asyncio
async def test_set_world_update(db, world_id):
    """Test updating an existing world."""
    result = await _set_world({
        "id": world_id,
        "name": "Updated World",
        "description": "Updated description",
    })
    
    assert len(result) == 1
    assert "Updated world" in result[0].text
    
    # Verify in database
    world = await db.worlds.find_one({"_id": ObjectId(world_id)})
    assert world["name"] == "Updated World"
    assert world["description"] == "Updated description"


@pytest.mark.asyncio
async def test_set_world_delete(db, world_id):
    """Test deleting a world."""
    result = await _set_world({
        "id": world_id,
        "delete": True,
    })
    
    assert len(result) == 1
    assert "Deleted world" in result[0].text
    
    # Verify in database
    world = await db.worlds.find_one({"_id": ObjectId(world_id)})
    assert world is None


@pytest.mark.asyncio
async def test_set_lore_create(db, world_id):
    """Test creating lore."""
    result = await _set_lore({
        "world_id": world_id,
        "title": "The Ancient War",
        "content": "Long ago, the gods fought...",
        "time_start": "1000 years before",
        "time_end": "500 years before",
        "tags": ["history", "war"],
    })
    
    assert len(result) == 1
    assert "Created lore" in result[0].text
    
    # Verify in database
    lore = await db.lore.find().to_list(100)
    assert len(lore) == 1
    assert lore[0]["title"] == "The Ancient War"


@pytest.mark.asyncio
async def test_set_location_create(db, world_id):
    """Test creating a location."""
    result = await _set_location({
        "world_id": world_id,
        "name": "The Dark Forest",
        "description": "A mysterious forest",
        "coordinates": {"x": 10, "y": 20},
        "tags": ["forest", "dangerous"],
    })
    
    assert len(result) == 1
    assert "Created location" in result[0].text
    
    # Verify in database
    locations = await db.locations.find({"name": "The Dark Forest"}).to_list(100)
    assert len(locations) == 1
    assert locations[0]["coordinates"]["coordinates"] == [10, 20]


@pytest.mark.asyncio
async def test_set_location_with_connections(db, world_id, location_id):
    """Test creating a location with connections."""
    result = await _set_location({
        "world_id": world_id,
        "name": "Hidden Cave",
        "description": "A secret cave",
        "connections": [
            {
                "location_id": location_id,
                "direction": "north",
                "description": "A narrow tunnel",
                "tags": ["hidden"],
            }
        ],
    })
    
    assert len(result) == 1
    assert "Created location" in result[0].text
    
    # Verify connections
    location = await db.locations.find_one({"name": "Hidden Cave"})
    assert len(location["connections"]) == 1
    assert location["connections"][0]["direction"] == "north"


@pytest.mark.asyncio
async def test_set_faction_create(db, world_id):
    """Test creating a faction."""
    result = await _set_faction({
        "world_id": world_id,
        "name": "The Red Army",
        "description": "A powerful military force",
        "type": "military",
        "tags": ["army", "evil"],
    })
    
    assert len(result) == 1
    assert "Created faction" in result[0].text
    
    # Verify in database
    factions = await db.factions.find().to_list(100)
    assert len(factions) == 1
    assert factions[0]["name"] == "The Red Army"
    assert factions[0]["type"] == "military"


@pytest.mark.asyncio
async def test_set_item_blueprint_create(db, world_id):
    """Test creating an item template."""
    result = await _set_item_blueprint({
        "world_id": world_id,
        "name": "Iron Sword",
        "description": "A sturdy iron sword",
        "stackable": False,
        "attributes": [
            {"name": "damage", "value": "1d8"},
            {"name": "weight", "value": 3},
        ],
        "tags": ["weapon", "sword"],
    })
    
    assert len(result) == 1
    assert "Created item blueprint" in result[0].text
    
    # Verify in database
    templates = await db.item_templates.find().to_list(100)
    assert len(templates) == 1
    assert templates[0]["name"] == "Iron Sword"
    assert templates[0]["stackable"] is False


@pytest.mark.asyncio
async def test_set_ability_blueprint_create(db, world_id):
    """Test creating an ability template."""
    result = await _set_ability_blueprint({
        "world_id": world_id,
        "name": "Fireball",
        "description": "Launches a ball of fire",
        "type": "spell",
        "cost": "10 MP",
        "effect": "Deals 3d6 fire damage in a 20ft radius",
        "tags": ["fire", "offensive", "aoe"],
    })
    
    assert len(result) == 1
    assert "Created ability blueprint" in result[0].text
    
    # Verify in database
    templates = await db.ability_templates.find().to_list(100)
    assert len(templates) == 1
    assert templates[0]["name"] == "Fireball"
    assert templates[0]["cost"] == "10 MP"
