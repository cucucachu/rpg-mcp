"""Character model."""

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId


class Attribute(BaseModel):
    """A character attribute (HP, MP, Strength, etc.)."""
    name: str
    value: Any
    max: Optional[Any] = None


class Skill(BaseModel):
    """A character skill/proficiency."""
    name: str
    value: Any


class CharacterAbility(BaseModel):
    """An ability a character can use."""
    template_id: Optional[str] = None
    name: str
    description: str = ""
    attributes: list[Attribute] = Field(default_factory=list)


class Status(BaseModel):
    """A status effect on a character."""
    name: str
    description: str = ""


class FactionMembership(BaseModel):
    """A character's membership in a faction."""
    faction_id: str
    rank: str = ""
    reputation: int = 0
    role: str = ""


class Character(BaseModel):
    """A player character or NPC."""
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(default=None, alias="_id")
    world_id: str
    is_player_character: bool = False
    name: str
    description: str = ""
    level: int = 1
    location_id: Optional[str] = None
    attributes: list[Attribute] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    abilities: list[CharacterAbility] = Field(default_factory=list)
    statuses: list[Status] = Field(default_factory=list)
    factions: list[FactionMembership] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    creation_in_progress: bool = Field(
        default=False,
        description="True while the character is being created; set to False when finalized.",
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
    def from_doc(cls, doc: dict) -> "Character":
        """Create from MongoDB document. Missing creation_in_progress => False (existing characters)."""
        d = dict(doc)
        if d.get("_id"):
            d["_id"] = str(d["_id"])
        if "creation_in_progress" not in d:
            d["creation_in_progress"] = False
        return cls(**d)
