# MCP Tools Audit

**Purpose:** Document which MCP tools are utilized by the agent pipeline, which are not, and identify any irrelevant or conflicting tools.

---

## 1. Tool Assignment by Agent

| Agent | Tools | Purpose |
|-------|-------|---------|
| **Historian** | `search_lore`, `find_characters`, `find_locations`, `find_events`, `find_quests`, `find_factions`, `get_entity`, `get_chronicle_details`, `get_location_contents`, `find_nearby_locations`, `get_character_inventory` | Read-only search to enrich context before GM |
| **Bard** | `create_character`, `rename_character`, `set_location`, `set_lore`, `set_faction` | Record new NPCs, locations, lore, factions from narrative |
| **GM** | **Dice**, **Encounters**, and **create_player_character** (PC creation only, with full stats: level, attributes, skills, abilities). No queries, quests, groups, or NPC entity creation. Context is pre-loaded; Bard/Accountant/Scribe handle state. | Narrative, game mechanics, and new PC creation |
| **Accountant** | `deal_damage`, `heal`, `apply_statuses`, `remove_status`, `set_attributes`, `set_skills`, `set_level`, `grant_abilities`, `revoke_ability`, `move_character`, `give_item`, `drop_item`, `set_item_quantity`, `spawn_item`, `destroy_item`, `set_item_attribute`, `apply_item_status`, `remove_item_status` | Sync game state (HP, status, items) from GM response |
| **Scribe** | `record_event`, `set_chronicle` | Record events and chronicles |

---

## 2. Tools by Module

### Registered Modules (server.py)

| Module | Tools | Agent(s) Using |
|--------|-------|----------------|
| **world_creation** | `set_world`, `set_lore`, `set_location`, `set_faction`, `set_item_blueprint`, `set_ability_blueprint` | Bard: set_lore, set_location, set_faction |
| **characters** | `create_character`, `create_player_character`, `delete_character`, `rename_character`, ... | Historian: find_characters; Bard: create_character, rename_character, set_location; Accountant: deal_damage, heal, set_attributes, ...; GM: create_player_character only |
| **items** | `spawn_item`, `destroy_item`, `give_item`, `drop_item`, `set_item_quantity`, `set_item_attribute`, `apply_item_status`, `remove_item_status` | Accountant: all; GM: spawn_item, give_item, etc. |
| **quests** | `create_quest`, `delete_quest`, `begin_quest`, `update_quest`, `complete_quest`, `record_event`, `set_chronicle`, `delete_event` | Historian: find_quests; Scribe: record_event, set_chronicle; GM: create_quest, begin_quest, etc. |
| **groups** | `form_party`, `disband_party`, `rename_party`, `add_to_party`, `remove_from_party`, `set_party_leader` | GM only |
| **queries** | `get_entity`, `find_characters`, `find_items`, `find_locations`, `find_nearby_locations`, `find_quests`, `find_events`, `search_lore`, `find_factions`, `find_parties`, `get_world_summary`, `get_location_contents`, `load_session`, `get_character_inventory`, `get_chronicle_details` | Historian: most; GM excluded: load_session |
| **dice_tools** | `roll_dice`, `roll_table`, `coin_flip`, `roll_stat_array`, `percentile_roll` | GM |
| **encounters** | `start_encounter`, `get_encounter`, `get_active_encounter`, `add_combatant`, `set_initiative`, `remove_combatant`, `next_turn`, `end_encounter` | GM |

### Not Registered (Removed)

| Module | Tools | Reason |
|--------|-------|--------|
| **time_tools** | `get_game_time`, `set_game_time`, `advance_game_time` | Game time now tracked via events; removed from server |

---

## 3. Tools NOT Used by Agents

| Tool | Module | Notes |
|------|--------|-------|
| `load_session` | queries | Explicitly excluded from GM; pipeline uses load_context node instead (world_context, events_context, etc.) |
| `set_world` | world_creation | Worlds created via rpg-agents API, not MCP |
| `set_item_blueprint`, `set_ability_blueprint` | world_creation | Pre-population / world-building; rarely used during play |
| `delete_character` | characters | Could be used by GM for narrative (NPC dies); not in Bard/Accountant |
| `delete_quest`, `delete_event` | quests | Rare; cleanup operations |
| `form_party`, `disband_party`, `rename_party`, `add_to_party`, `remove_from_party`, `set_party_leader` | groups | GM has these; used when party dynamics change |
| `get_character_inventory` | queries | Assigned to Historian for context |

---

## 4. Potential Conflicts / Redundancies

### 4.1 record_event (events only from Scribe)

- **Quests module:** `record_event` creates events.
- **Scribe agent:** Sole user of `record_event`; events are only created explicitly by the Scribe.
- **Accountant:** Uses `deal_damage` and `heal` – these **do not create events**; they only update character state. The Scribe records damage/healing from the narrative.
- **encounters:** `end_encounter` no longer creates events; the Scribe records encounter endings from the narrative.

### 4.2 Entity Creation (Bard only)

- **Bard:** Creates characters, locations, lore, factions.
- **GM:** No longer has `create_character`, `set_location`, `set_faction`. GM narrates; Bard formalizes and records entities.

### 4.3 load_session vs load_context

- **MCP `load_session`:** Returns PCs, quests, chronicles, events, parties.
- **Pipeline `load_context`:** Loads world, PCs, quests, events since chronicle, builds world_context JSON.
- **Verdict:** Pipeline does its own loading; `load_session` is excluded from GM to avoid redundancy. `load_session` could be useful for external tools (e.g. a "resume session" UI) but not for the GM agent.

---

## 5. Recommendations

### Keep As-Is

- **Time tools:** Correctly removed; game time derived from events.
- **Tool separation:** Historian (read) | Bard (entity creation) | GM (narration + tools) | Accountant (state sync) | Scribe (events/chronicles) is clean.
- **Party tools:** GM has them; used when party composition changes.

### Consider

1. **`get_character_inventory` for Historian:** If the Historian needs to know "what does Thorne have?" for context, add it to historian_tool_names. Currently not used.
2. **`delete_character` for Bard/Accountant:** If an NPC permanently leaves/dies, should Bard or Accountant remove them? Currently neither has `delete_character`; GM has it. Probably fine – GM handles dramatic removals.
3. **Accountant tools:** `deal_damage` and `heal` no longer create events. Events are recorded only by the Scribe.

### No Action

- **set_item_blueprint, set_ability_blueprint:** World-building tools; fine to keep for pre-campaign setup.
- **delete_quest, delete_event:** Rare cleanup; keep for flexibility.

---

## 6. Summary

| Category | Count | Notes |
|----------|-------|-------|
| **Tools registered** | ~55 | Across 8 modules |
| **Tools used by agents** | ~45 | Most tools are utilized |
| **Tools excluded (GM)** | `load_session` | Pipeline uses load_context |
| **Tools removed** | `get_game_time`, `set_game_time`, `advance_game_time` | Game time from events |
| **Conflicts** | None critical | Some overlap (events, entity creation) is intentional |
