"""Lore model."""

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId

from .quest import RelatedEntity


class Lore(BaseModel):
    """World-building and historical information."""
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(default=None, alias="_id")
    world_id: str
    title: str
    content: str = ""  # the lore text, freeform
    time_start: str = ""  # freeform, e.g., "1000 years before"
    time_end: str = ""  # freeform, e.g., "500 years before"
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
    def from_doc(cls, doc: dict) -> "Lore":
        """Create from MongoDB document."""
        if doc.get("_id"):
            doc["_id"] = str(doc["_id"])
        return cls(**doc)
