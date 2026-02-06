"""MongoDB connection management."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional

from .config import settings


class Database:
    """MongoDB database connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.db_name]
        
        # Create indexes
        await self._create_indexes()
        
    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            
    async def _create_indexes(self) -> None:
        """Create necessary indexes for collections."""
        # World
        await self.db.worlds.create_index("name")
        
        # Characters
        await self.db.characters.create_index("world_id")
        await self.db.characters.create_index("location_id")
        await self.db.characters.create_index([("world_id", 1), ("name", 1)])
        
        # Items
        await self.db.items.create_index("world_id")
        await self.db.items.create_index("owner_id")
        await self.db.items.create_index("location_id")
        await self.db.items.create_index("template_id")
        
        # Item templates
        await self.db.item_templates.create_index("world_id")
        
        # Ability templates
        await self.db.ability_templates.create_index("world_id")
        
        # Locations - including geospatial index
        await self.db.locations.create_index("world_id")
        await self.db.locations.create_index("parent_location_id")
        await self.db.locations.create_index([("coordinates", "2dsphere")])
        
        # Factions
        await self.db.factions.create_index("world_id")
        
        # Parties
        await self.db.parties.create_index("world_id")
        await self.db.parties.create_index("members")
        
        # Quests
        await self.db.quests.create_index("world_id")
        await self.db.quests.create_index("status")
        await self.db.quests.create_index("assigned_to")
        
        # Events
        await self.db.events.create_index("world_id")
        await self.db.events.create_index([("world_id", 1), ("game_time", 1)])
        await self.db.events.create_index("location_id")
        
        # Chronicles
        await self.db.chronicles.create_index("world_id")
        await self.db.chronicles.create_index([("world_id", 1), ("game_time_start", 1)])
        
        # Lore - including text index for full-text search
        await self.db.lore.create_index("world_id")
        await self.db.lore.create_index([("title", "text"), ("content", "text")])


# Global database instance
database = Database()
