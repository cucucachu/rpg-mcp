"""Faction model."""

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId

from .character import Attribute


class FactionRelationship(BaseModel):
    """Relationship between two factions."""
    faction_id: str
    status: str  # allied, neutral, hostile, war, vassal, etc.
    description: str = ""


class Faction(BaseModel):
    """A formal organization."""
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(default=None, alias="_id")
    world_id: str
    name: str
    description: str = ""
    type: str = ""  # military, guild, government, religious, criminal
    headquarters_id: Optional[str] = None
    leader_id: Optional[str] = None
    relationships: list[FactionRelationship] = Field(default_factory=list)
    attributes: list[Attribute] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def to_doc(self) -> dict:
        """Convert to MongoDB document."""
        doc = self.model_dump(by_alias=True, exclude_none=True)
        if doc.get("_id"):
            doc["_id"] = ObjectId(doc["_id"])
        else:
            doc.pop("_id", None)
        return doc
    
    @classmethod
    def from_doc(cls, doc: dict) -> "Faction":
        """Create from MongoDB document."""
        if doc.get("_id"):
            doc["_id"] = str(doc["_id"])
        return cls(**doc)
