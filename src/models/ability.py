"""AbilityTemplate model."""

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId

from .character import Attribute


class AbilityTemplate(BaseModel):
    """A blueprint for an ability/spell/skill."""
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(default=None, alias="_id")
    world_id: str
    name: str
    description: str = ""
    type: str = ""  # spell, attack, passive, etc.
    cost: str = ""  # freeform: "10 MP", "1 action"
    effect: str = ""  # freeform description of what it does
    requirements: str = ""  # freeform: "Level 5", "Fire affinity"
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
    def from_doc(cls, doc: dict) -> "AbilityTemplate":
        """Create from MongoDB document."""
        if doc.get("_id"):
            doc["_id"] = str(doc["_id"])
        return cls(**doc)
