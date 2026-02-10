"""Tests for query tools."""

import pytest
import json
from bson import ObjectId

from src.tools.queries import (
    _get_entity,
    _find_characters,
    _find_items,
    _find_locations,
    _find_quests,
    _get_world_summary,
    _get_location_contents,
    _load_session,
    _get_character_inventory,
)


@pytest.mark.asyncio
async def test_get_entity_world(db, world_id):
    """Test getting a world entity."""
    result = await _get_entity({
        "collection": "world",
        "id": world_id,
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["name"] == "Test World"


@pytest.mark.asyncio
async def test_get_entity_character(db, character_id):
    """Test getting a character entity."""
    result = await _get_entity({
        "collection": "character",
        "id": character_id,
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["name"] == "Test Character"


@pytest.mark.asyncio
async def test_find_characters(db, world_id, character_id):
    """Test finding characters."""
    result = await _find_characters({
        "world_id": world_id,
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert len(data) == 1
    assert data[0]["name"] == "Test Character"


@pytest.mark.asyncio
async def test_find_characters_by_location(db, world_id, location_id, character_id):
    """Test finding characters at a location."""
    result = await _find_characters({
        "world_id": world_id,
        "location_id": location_id,
    })
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert len(data) == 1
    assert data[0]["id"] == character_id


@pytest.mark.asyncio
async def test_find_characters_pc_only(db, world_id, character_id):
    """Test finding only player characters."""
    # Add an NPC
    await db.characters.insert_one({
        "world_id": world_id,
        "name": "NPC",
        "is_player_character": False,
    })
    
    result = await _find_characters({
        "world_id": world_id,
        "is_player_character": True,
    })
    
    data = json.loads(result[0].text)
    assert len(data) == 1
    assert data[0]["is_player_character"] is True


@pytest.mark.asyncio
async def test_find_items(db, world_id, character_id):
    """Test finding items."""
    # Create some items
    await db.items.insert_one({
        "world_id": world_id,
        "name": "Sword",
        "owner_id": character_id,
    })
    await db.items.insert_one({
        "world_id": world_id,
        "name": "Shield",
        "owner_id": character_id,
    })
    
    result = await _find_items({
        "world_id": world_id,
    })
    
    data = json.loads(result[0].text)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_find_items_by_owner(db, world_id, character_id):
    """Test finding items by owner."""
    # Create items with different owners
    await db.items.insert_one({
        "world_id": world_id,
        "name": "Sword",
        "owner_id": character_id,
    })
    await db.items.insert_one({
        "world_id": world_id,
        "name": "Lost Item",
        "owner_id": None,
    })
    
    result = await _find_items({
        "world_id": world_id,
        "owner_id": character_id,
    })
    
    data = json.loads(result[0].text)
    assert len(data) == 1
    assert data[0]["name"] == "Sword"


@pytest.mark.asyncio
async def test_find_locations(db, world_id, location_id):
    """Test finding locations."""
    result = await _find_locations({
        "world_id": world_id,
    })
    
    data = json.loads(result[0].text)
    assert len(data) == 1
    assert data[0]["name"] == "Test Location"


@pytest.mark.asyncio
async def test_find_quests(db, world_id, character_id):
    """Test finding quests."""
    # Create quests
    await db.quests.insert_one({
        "world_id": world_id,
        "name": "Main Quest",
        "status": "active",
        "assigned_to": [character_id],
    })
    await db.quests.insert_one({
        "world_id": world_id,
        "name": "Side Quest",
        "status": "available",
        "assigned_to": [],
    })
    
    result = await _find_quests({
        "world_id": world_id,
        "status": "active",
    })
    
    data = json.loads(result[0].text)
    assert len(data) == 1
    assert data[0]["name"] == "Main Quest"


@pytest.mark.asyncio
async def test_get_world_summary(db, world_id, character_id, location_id):
    """Test getting world summary."""
    # Add some data
    await db.quests.insert_one({
        "world_id": world_id,
        "name": "Active Quest",
        "status": "active",
    })
    await db.parties.insert_one({
        "world_id": world_id,
        "name": "Heroes",
        "members": [character_id],
    })
    
    result = await _get_world_summary({
        "world_id": world_id,
    })
    
    data = json.loads(result[0].text)
    assert data["world"]["name"] == "Test World"
    assert data["counts"]["characters"] == 1
    assert data["counts"]["locations"] == 1
    assert len(data["active_quests"]) == 1
    assert len(data["parties"]) == 1


@pytest.mark.asyncio
async def test_get_location_contents(db, world_id, character_id, location_id):
    """Test getting location contents."""
    # Add an item at the location
    await db.items.insert_one({
        "world_id": world_id,
        "name": "Treasure",
        "location_id": location_id,
    })
    
    result = await _get_location_contents({
        "location_id": location_id,
    })
    
    data = json.loads(result[0].text)
    assert data["location"]["name"] == "Test Location"
    assert len(data["characters"]) == 1
    assert data["characters"][0]["name"] == "Test Character"
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Treasure"


@pytest.mark.asyncio
async def test_load_session(db, world_id, character_id, location_id):
    """Test loading full session context."""
    # Add HP attribute to character
    await db.characters.update_one(
        {"_id": ObjectId(character_id)},
        {"$set": {"attributes": [{"name": "HP", "value": 25, "max": 30}]}}
    )
    
    # Add active quest
    await db.quests.insert_one({
        "world_id": world_id,
        "name": "Save the Village",
        "description": "Defend against goblins",
        "status": "active",
        "assigned_to": [character_id],
        "progress": "Scouted enemy camp",
    })
    
    # Add chronicle
    await db.chronicles.insert_one({
        "world_id": world_id,
        "title": "Session 1: The Beginning",
        "summary": "Heroes met in a tavern",
        "consequences": "Party formed",
        "game_time_start": 0,
        "game_time_end": 60,
        "significance": "major",
    })
    
    # Add event
    await db.events.insert_one({
        "world_id": world_id,
        "name": "Goblin Sighting",
        "description": "Goblins spotted near town",
        "game_time": 30,
        "location_id": location_id,
    })
    
    result = await _load_session({
        "world_id": world_id,
    })
    
    data = json.loads(result[0].text)
    
    # Verify world (game_time derived from events/chronicles)
    assert data["world"]["name"] == "Test World"
    assert data["game_time"]["raw"] == 60  # max(event 30, chronicle_end 60)
    assert "formatted" in data["game_time"]
    
    # Verify PC
    assert len(data["player_characters"]) == 1
    pc = data["player_characters"][0]
    assert pc["name"] == "Test Character"
    assert pc["hp_current"] == 25
    assert pc["hp_max"] == 30
    assert pc["location_name"] == "Test Location"
    
    # Verify quest
    assert len(data["active_quests"]) == 1
    assert data["active_quests"][0]["name"] == "Save the Village"
    assert data["active_quests"][0]["progress"] == "Scouted enemy camp"
    
    # Verify chronicle
    assert len(data["recent_chronicles"]) == 1
    assert data["recent_chronicles"][0]["title"] == "Session 1: The Beginning"
    assert data["recent_chronicles"][0]["summary"] == "Heroes met in a tavern"
    
    # Verify events
    assert len(data["recent_events"]) == 1
    assert data["recent_events"][0]["description"] == "Goblins spotted near town"
    
    # Verify counts
    assert data["counts"]["total_characters"] == 1
    assert data["counts"]["total_locations"] == 1


@pytest.mark.asyncio
async def test_load_session_limits(db, world_id, character_id, location_id):
    """Test load_session respects limits."""
    # Add multiple chronicles
    for i in range(5):
        await db.chronicles.insert_one({
            "world_id": world_id,
            "title": f"Chronicle {i}",
            "summary": f"Summary {i}",
            "game_time_start": i * 100,
            "game_time_end": (i + 1) * 100,
        })
    
    # Add multiple events
    for i in range(15):
        await db.events.insert_one({
            "world_id": world_id,
            "name": f"Event {i}",
            "description": f"Description {i}",
            "game_time": i * 10,
        })
    
    result = await _load_session({
        "world_id": world_id,
        "chronicle_limit": 2,
        "event_limit": 5,
    })
    
    data = json.loads(result[0].text)
    assert len(data["recent_chronicles"]) == 2
    assert len(data["recent_events"]) == 5


@pytest.mark.asyncio
async def test_get_character_inventory(db, world_id, character_id):
    """Test getting character inventory."""
    # Add items owned by character
    await db.items.insert_one({
        "world_id": world_id,
        "name": "Sword",
        "description": "A sharp blade",
        "owner_id": character_id,
        "quantity": 1,
        "tags": ["weapon"],
    })
    await db.items.insert_one({
        "world_id": world_id,
        "name": "Gold Coins",
        "description": "Currency",
        "owner_id": character_id,
        "quantity": 50,
        "tags": ["currency"],
    })
    # Item not owned by this character
    await db.items.insert_one({
        "world_id": world_id,
        "name": "Treasure Chest",
        "owner_id": None,
    })
    
    result = await _get_character_inventory({
        "character_id": character_id,
    })
    
    data = json.loads(result[0].text)
    assert data["character_name"] == "Test Character"
    assert data["total_items"] == 2
    assert len(data["items"]) == 2
    
    # Verify item details
    item_names = [item["name"] for item in data["items"]]
    assert "Sword" in item_names
    assert "Gold Coins" in item_names
    
    # Check quantity is included
    gold = next(i for i in data["items"] if i["name"] == "Gold Coins")
    assert gold["quantity"] == 50


@pytest.mark.asyncio
async def test_get_character_inventory_not_found(db):
    """Test getting inventory for non-existent character."""
    fake_id = str(ObjectId())
    
    result = await _get_character_inventory({
        "character_id": fake_id,
    })
    
    assert "not found" in result[0].text
