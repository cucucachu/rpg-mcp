"""Party model."""

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId


class Party(BaseModel):
    """An informal group of characters."""
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(default=None, alias="_id")
    world_id: str
    name: str = ""
    description: str = ""
    members: list[str] = Field(default_factory=list)  # character_ids
    leader_id: Optional[str] = None
    formed_at: int = 0  # game_time when party was created
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
    def from_doc(cls, doc: dict) -> "Party":
        """Create from MongoDB document."""
        if doc.get("_id"):
            doc["_id"] = str(doc["_id"])
        return cls(**doc)
