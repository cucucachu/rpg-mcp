"""Location model."""

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId

from .character import Attribute


class GeoJSONPoint(BaseModel):
    """GeoJSON Point for location coordinates."""
    type: str = "Point"
    coordinates: list[float]  # [x, y]


class GeoJSONPolygon(BaseModel):
    """GeoJSON Polygon for location bounds."""
    type: str = "Polygon"
    coordinates: list[list[list[float]]]  # [[[x1,y1], [x2,y2], ...]]


class Connection(BaseModel):
    """A connection/passage to another location."""
    location_id: str
    direction: str = ""  # north, south, up, down, etc.
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class Location(BaseModel):
    """A place in the world."""
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(default=None, alias="_id")
    world_id: str
    name: str
    description: str = ""
    parent_location_id: Optional[str] = None
    coordinates: Optional[GeoJSONPoint] = None
    bounds: Optional[GeoJSONPolygon] = None
    connections: list[Connection] = Field(default_factory=list)
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
    def from_doc(cls, doc: dict) -> "Location":
        """Create from MongoDB document."""
        if doc.get("_id"):
            doc["_id"] = str(doc["_id"])
        return cls(**doc)
