"""Event model."""

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId


class Event(BaseModel):
    """A game event (state change record)."""
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(default=None, alias="_id")
    world_id: str
    game_time: int  # seconds since game start
    location_id: Optional[str] = None
    name: str
    description: str = ""
    participants: str = ""  # freeform
    changes: str = ""  # freeform
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
    def from_doc(cls, doc: dict) -> "Event":
        """Create from MongoDB document."""
        if doc.get("_id"):
            doc["_id"] = str(doc["_id"])
        return cls(**doc)
