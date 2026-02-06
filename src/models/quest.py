"""Quest model."""

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId


class RelatedEntity(BaseModel):
    """A reference to a related entity."""
    entity_type: str  # character, location, item, etc.
    entity_id: str


class Quest(BaseModel):
    """A quest/mission."""
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(default=None, alias="_id")
    world_id: str
    name: str
    description: str = ""
    status: str = "available"  # available, active, completed, failed, etc.
    giver_id: Optional[str] = None  # character who gave the quest
    assigned_to: list[str] = Field(default_factory=list)  # character_ids
    objectives: str = ""  # freeform
    progress: str = ""  # freeform
    rewards: str = ""  # freeform
    time_limit: Optional[int] = None  # game_time seconds
    related_entities: list[RelatedEntity] = Field(default_factory=list)
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
    def from_doc(cls, doc: dict) -> "Quest":
        """Create from MongoDB document."""
        if doc.get("_id"):
            doc["_id"] = str(doc["_id"])
        return cls(**doc)
