"""World model."""

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId


class World(BaseModel):
    """A game world container."""
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    description: str = ""
    settings: dict[str, Any] = Field(default_factory=dict)
    creation_in_progress: bool = Field(
        default=True,
        description="True while the world is being set up; set to False when the GM calls start_game.",
    )
    
    def to_doc(self) -> dict:
        """Convert to MongoDB document."""
        doc = self.model_dump(by_alias=True, exclude_none=True)
        if doc.get("_id"):
            doc["_id"] = ObjectId(doc["_id"])
        else:
            doc.pop("_id", None)
        return doc
    
    @classmethod
    def from_doc(cls, doc: dict) -> "World":
        """Create from MongoDB document. Ignores legacy game_time. Missing creation_in_progress => False (existing worlds)."""
        d = dict(doc)
        if d.get("_id"):
            d["_id"] = str(d["_id"])
        d.pop("game_time", None)
        if "creation_in_progress" not in d:
            d["creation_in_progress"] = False
        return cls(**d)
