"""Pytest fixtures for RPG MCP tests."""

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from src.config import settings
from src.db import database


@pytest_asyncio.fixture
async def db():
    """Provide a clean database for each test."""
    # Connect to test database
    client = AsyncIOMotorClient(settings.mongodb_uri)
    test_db = client[settings.db_name]
    
    # Set the database on our global database object
    database.client = client
    database.db = test_db
    
    # Create indexes
    await database._create_indexes()
    
    yield test_db
    
    # Clean up: drop all collections after test
    collections = await test_db.list_collection_names()
    for collection in collections:
        await test_db.drop_collection(collection)
    
    client.close()


@pytest_asyncio.fixture
async def world_id(db):
    """Create a test world and return its ID."""
    result = await db.worlds.insert_one({
        "name": "Test World",
        "description": "A world for testing",
        "settings": {},
        "game_time": 0,
    })
    return str(result.inserted_id)


@pytest_asyncio.fixture
async def location_id(db, world_id):
    """Create a test location and return its ID."""
    result = await db.locations.insert_one({
        "world_id": world_id,
        "name": "Test Location",
        "description": "A location for testing",
        "coordinates": {"type": "Point", "coordinates": [0, 0]},
    })
    return str(result.inserted_id)


@pytest_asyncio.fixture
async def character_id(db, world_id, location_id):
    """Create a test character and return its ID."""
    result = await db.characters.insert_one({
        "world_id": world_id,
        "name": "Test Character",
        "description": "A character for testing",
        "is_player_character": True,
        "level": 1,
        "location_id": location_id,
        "attributes": [],
        "skills": [],
        "abilities": [],
        "statuses": [],
        "factions": [],
        "tags": [],
    })
    return str(result.inserted_id)
