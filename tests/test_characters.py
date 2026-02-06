"""Tests for character tools."""

import pytest
from bson import ObjectId

from src.tools.characters import (
    _create_character,
    _delete_character,
    _rename_character,
    _move_character,
    _set_level,
    _set_attribute,
    _set_skill,
    _grant_ability,
    _revoke_ability,
    _apply_status,
    _remove_status,
    _join_faction,
    _leave_faction,
    _set_faction_standing,
)


@pytest.mark.asyncio
async def test_create_character(db, world_id, location_id):
    """Test creating a character."""
    result = await _create_character({
        "world_id": world_id,
        "name": "Hero",
        "description": "A brave adventurer",
        "is_player_character": True,
        "location_id": location_id,
    })
    
    assert len(result) == 1
    assert "Created character" in result[0].text
    assert "Hero" in result[0].text
    
    # Verify in database
    characters = await db.characters.find().to_list(100)
    assert len(characters) == 1
    assert characters[0]["name"] == "Hero"
    assert characters[0]["is_player_character"] is True


@pytest.mark.asyncio
async def test_delete_character(db, character_id):
    """Test deleting a character."""
    result = await _delete_character({"character_id": character_id})
    
    assert len(result) == 1
    assert "Deleted character" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert character is None


@pytest.mark.asyncio
async def test_rename_character(db, character_id):
    """Test renaming a character."""
    result = await _rename_character({
        "character_id": character_id,
        "name": "New Name",
        "description": "New description",
    })
    
    assert len(result) == 1
    assert "Updated character" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert character["name"] == "New Name"
    assert character["description"] == "New description"


@pytest.mark.asyncio
async def test_move_character(db, world_id, character_id):
    """Test moving a character."""
    # Create a new location
    new_location = await db.locations.insert_one({
        "world_id": world_id,
        "name": "New Location",
    })
    new_location_id = str(new_location.inserted_id)
    
    result = await _move_character({
        "character_id": character_id,
        "location_id": new_location_id,
    })
    
    assert len(result) == 1
    assert "Moved character" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert character["location_id"] == new_location_id


@pytest.mark.asyncio
async def test_set_level(db, character_id):
    """Test setting character level."""
    result = await _set_level({
        "character_id": character_id,
        "level": 5,
    })
    
    assert len(result) == 1
    assert "Set level" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert character["level"] == 5


@pytest.mark.asyncio
async def test_set_attribute(db, character_id):
    """Test setting a character attribute."""
    result = await _set_attribute({
        "character_id": character_id,
        "name": "HP",
        "value": 20,
        "max": 25,
    })
    
    assert len(result) == 1
    assert "Set attribute" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert len(character["attributes"]) == 1
    assert character["attributes"][0]["name"] == "HP"
    assert character["attributes"][0]["value"] == 20
    assert character["attributes"][0]["max"] == 25


@pytest.mark.asyncio
async def test_set_skill(db, character_id):
    """Test setting a character skill."""
    result = await _set_skill({
        "character_id": character_id,
        "name": "Stealth",
        "value": 15,
    })
    
    assert len(result) == 1
    assert "Set skill" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert len(character["skills"]) == 1
    assert character["skills"][0]["name"] == "Stealth"
    assert character["skills"][0]["value"] == 15


@pytest.mark.asyncio
async def test_grant_ability(db, character_id):
    """Test granting an ability to a character."""
    result = await _grant_ability({
        "character_id": character_id,
        "name": "Fireball",
        "description": "Throws a ball of fire",
    })
    
    assert len(result) == 1
    assert "Granted ability" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert len(character["abilities"]) == 1
    assert character["abilities"][0]["name"] == "Fireball"


@pytest.mark.asyncio
async def test_revoke_ability(db, character_id):
    """Test revoking an ability from a character."""
    # First grant an ability
    await _grant_ability({
        "character_id": character_id,
        "name": "Fireball",
        "description": "Throws a ball of fire",
    })
    
    # Then revoke it
    result = await _revoke_ability({
        "character_id": character_id,
        "ability_name": "Fireball",
    })
    
    assert len(result) == 1
    assert "Revoked ability" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert len(character["abilities"]) == 0


@pytest.mark.asyncio
async def test_apply_status(db, character_id):
    """Test applying a status to a character."""
    result = await _apply_status({
        "character_id": character_id,
        "name": "Poisoned",
        "description": "Losing 1 HP per turn",
    })
    
    assert len(result) == 1
    assert "Applied status" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert len(character["statuses"]) == 1
    assert character["statuses"][0]["name"] == "Poisoned"


@pytest.mark.asyncio
async def test_remove_status(db, character_id):
    """Test removing a status from a character."""
    # First apply a status
    await _apply_status({
        "character_id": character_id,
        "name": "Poisoned",
    })
    
    # Then remove it
    result = await _remove_status({
        "character_id": character_id,
        "name": "Poisoned",
    })
    
    assert len(result) == 1
    assert "Removed status" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert len(character["statuses"]) == 0


@pytest.mark.asyncio
async def test_join_faction(db, world_id, character_id):
    """Test joining a faction."""
    # Create a faction
    faction = await db.factions.insert_one({
        "world_id": world_id,
        "name": "Thieves Guild",
    })
    faction_id = str(faction.inserted_id)
    
    result = await _join_faction({
        "character_id": character_id,
        "faction_id": faction_id,
        "rank": "initiate",
        "reputation": 10,
    })
    
    assert len(result) == 1
    assert "Joined faction" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert len(character["factions"]) == 1
    assert character["factions"][0]["faction_id"] == faction_id
    assert character["factions"][0]["rank"] == "initiate"


@pytest.mark.asyncio
async def test_leave_faction(db, world_id, character_id):
    """Test leaving a faction."""
    # Create and join a faction
    faction = await db.factions.insert_one({
        "world_id": world_id,
        "name": "Thieves Guild",
    })
    faction_id = str(faction.inserted_id)
    
    await _join_faction({
        "character_id": character_id,
        "faction_id": faction_id,
    })
    
    # Leave the faction
    result = await _leave_faction({
        "character_id": character_id,
        "faction_id": faction_id,
    })
    
    assert len(result) == 1
    assert "Left faction" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert len(character["factions"]) == 0


@pytest.mark.asyncio
async def test_set_faction_standing(db, world_id, character_id):
    """Test updating faction standing."""
    # Create and join a faction
    faction = await db.factions.insert_one({
        "world_id": world_id,
        "name": "Thieves Guild",
    })
    faction_id = str(faction.inserted_id)
    
    await _join_faction({
        "character_id": character_id,
        "faction_id": faction_id,
        "rank": "initiate",
        "reputation": 10,
    })
    
    # Update standing
    result = await _set_faction_standing({
        "character_id": character_id,
        "faction_id": faction_id,
        "rank": "master",
        "reputation": 100,
    })
    
    assert len(result) == 1
    assert "Updated faction standing" in result[0].text
    
    # Verify in database
    character = await db.characters.find_one({"_id": ObjectId(character_id)})
    assert character["factions"][0]["rank"] == "master"
    assert character["factions"][0]["reputation"] == 100
