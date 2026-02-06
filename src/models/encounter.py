"""Encounter model for combat/turn-based scenes."""

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from bson import ObjectId


class Combatant(BaseModel):
    """A participant in an encounter."""
    character_id: str
    initiative: float = 0  # Any number - higher goes first
    is_active: bool = True  # False if fled, dead, etc.
    notes: str = ""  # GM notes for this combatant


class Encounter(BaseModel):
    """A turn-based encounter (combat, chase, social challenge, etc.)."""
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[str] = Field(default=None, alias="_id")
    world_id: str
    name: str = ""  # "Ambush at the Bridge", "Bar Brawl", etc.
    location_id: Optional[str] = None
    
    # Turn tracking
    combatants: list[Combatant] = Field(default_factory=list)
    current_turn: int = 0  # Index into sorted combatants
    round_number: int = 1
    
    # State
    status: str = "active"  # active, paused, ended
    started_at: Optional[int] = None  # game_time when started
    ended_at: Optional[int] = None  # game_time when ended
    
    # Metadata
    encounter_type: str = "combat"  # combat, chase, social, custom
    summary: str = ""  # Filled in when encounter ends
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def get_turn_order(self) -> list[Combatant]:
        """Return combatants sorted by initiative (highest first)."""
        return sorted(
            [c for c in self.combatants if c.is_active],
            key=lambda c: c.initiative,
            reverse=True
        )
    
    def get_current_combatant(self) -> Optional[Combatant]:
        """Get the combatant whose turn it is."""
        order = self.get_turn_order()
        if not order:
            return None
        # Wrap around if needed
        idx = self.current_turn % len(order)
        return order[idx]
    
    def to_doc(self) -> dict:
        """Convert to MongoDB document."""
        doc = self.model_dump(by_alias=True, exclude_none=True)
        if doc.get("_id"):
            doc["_id"] = ObjectId(doc["_id"])
        else:
            doc.pop("_id", None)
        return doc
    
    @classmethod
    def from_doc(cls, doc: dict) -> "Encounter":
        """Create from MongoDB document."""
        if doc.get("_id"):
            doc["_id"] = str(doc["_id"])
        return cls(**doc)
