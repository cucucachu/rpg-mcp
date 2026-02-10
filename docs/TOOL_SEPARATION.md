# Tool Separation: NPC vs PC

This document explains the separation between NPC and PC tools to ensure clear boundaries between agent responsibilities.

## Philosophy

- **World Creator**: Builds the world (lore, locations, factions, NPCs). Cannot touch Player Characters.
- **Character Creator**: Sets up Player Character stats and mechanics. Cannot create NPCs.
- **Bard**: Creates NPCs that emerge during gameplay narrative. Cannot touch PCs.
- **GM/Accountant**: General gameplay tools that work on any character during active play.

## Tool Categories

### NPC-Specific Tools (World Creator & Bard)

**For world building and narrative NPCs:**
- `create_npc` - Create NPCs with optional stats (level, HP, attributes, skills, abilities)
  - Hardcodes `is_player_character=false`
  - Can include full stat blocks
  - Used by World Creator for pre-built NPCs
  - Used by Bard for narrative-emergent NPCs
- `update_npc` - Update NPC name/description/level
  - Enforces `is_player_character=false` in query
  - Simple updates for existing NPCs
- `spawn_enemies` - Batch-create multiple NPCs for encounters
  - Specialized tool for combat encounters
  - All created characters are NPCs

### PC-Specific Tools (Character Creator)

**For player character setup:**
- `update_pc_basics` - Update PC name and description
  - Used during character creation
  - Only for PCs
- `set_attributes` - Set HP, ability scores, resources
  - Format: `[{name, value, max}, ...]`
- `set_skills` - Set proficiencies and bonuses
  - Format: `[{name, value}, ...]`
- `grant_abilities` - Add spells, features, attacks
  - Format: `[{name, description, attributes}, ...]`
- `finalize_character` - Mark character creation complete
  - Sets `creation_in_progress=false`

### General Gameplay Tools (GM & Accountant)

**Work on any character during gameplay:**
- `deal_damage` - Reduce HP, handle unconsciousness
- `heal` - Restore HP, remove unconsciousness
- `move_character` - Change location
- `apply_statuses` / `remove_status` - Status effects
- `set_level` - Level up/down
- `join_faction` / `leave_faction` / `set_faction_standing` - Faction membership

### Deprecated/Legacy Tools

**Still exist for backward compatibility but discouraged:**
- `create_character` - Use `create_npc` instead
- `rename_character` - Use `update_pc_basics` or `update_npc` instead
- `create_player_character` - Not used by agents (API creates skeleton PCs)

## Agent Tool Assignments

### World Creator
```python
world_creator_tool_names = {
    # Search/query
    "search_lore", "find_characters", "find_locations", "find_events",
    "find_quests", "find_factions", "get_entity", "get_location_contents", "find_nearby_locations",
    # Create/record (NPCs, locations, factions, lore)
    "set_lore", "set_location", "set_faction",
    "create_npc", "update_npc", "spawn_enemies",  # NPC-specific
    "set_item_blueprint", "set_ability_blueprint",
    # World basics
    "update_world_basics", "start_game",
    # Dice/random
    "roll_table", "coin_flip",
}
```

### Character Creator
```python
char_creator_tool_names = {
    # Update PC
    "update_pc_basics", "set_attributes", "set_skills", "grant_abilities",
    # Finalize
    "finalize_character",
    # Dice
    "roll_dice", "roll_stat_array", "roll_table",
    # Search
    "search_lore", "find_locations", "get_entity",
}
```

### Bard
```python
bard_tool_names = {
    "create_npc", "update_npc", "set_location",
    "set_lore", "set_faction",
}
```

## Implementation Details

### create_npc Handler
```python
async def _create_npc(args: dict[str, Any]) -> list[TextContent]:
    """Create a new NPC with optional stats."""
    # ... parse attributes, skills, abilities ...
    
    character = Character(
        world_id=args["world_id"],
        name=args["name"],
        description=args.get("description", ""),
        is_player_character=False,  # Hardcoded
        # ... stats ...
    )
```

### update_npc Handler
```python
async def _update_npc(args: dict[str, Any]) -> list[TextContent]:
    """Update an existing NPC's basic properties."""
    await db.characters.update_one(
        {"_id": ObjectId(args["character_id"]), "is_player_character": False},  # Enforced
        {"$set": update_data}
    )
```

## Benefits

1. **Impossible to cross boundaries**: World creator literally cannot modify PCs (no tool available)
2. **Clear tool naming**: `create_npc` vs `update_pc_basics` is unambiguous
3. **Type safety at tool level**: NPC tools enforce `is_player_character=false` in queries
4. **Better prompting**: Tools clearly signal intent ("This is for NPCs only")
5. **Easier debugging**: If a PC gets modified during world creation, we know there's a tool leak

## Migration Notes

- Old `create_character` calls with `is_player_character=false` should migrate to `create_npc`
- Old `rename_character` calls need context:
  - For PCs during creation: use `update_pc_basics`
  - For NPCs: use `update_npc`
- Both legacy tools still work but are marked deprecated
