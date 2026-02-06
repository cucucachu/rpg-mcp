# RPG MCP Server

A Model Context Protocol (MCP) server for managing RPG game data. This server provides a game-system-agnostic backend for AI agents to create and manage RPG worlds, characters, items, quests, and more.

## Architecture

- **Python 3.12** with async/await throughout
- **MCP SDK** with SSE transport for networked access
- **MongoDB** for flexible document storage
- **Docker Compose** for local development and testing

## Features

### World Creation
- Create and manage game worlds with custom settings
- Define locations with hierarchy, geo-coordinates, and connections
- Establish factions and their relationships
- Create item and ability blueprints (templates)
- Write lore and world history

### Gameplay Management
- Create and manage characters (PCs and NPCs)
- Track attributes, skills, abilities, and status effects
- Manage inventory with item instances
- Create and track quests
- Record events and write story chronicles
- Form parties and manage faction membership
- Track in-game time

### Queries
- Search characters, items, locations by various criteria
- Geo-spatial queries for nearby locations
- Full-text search through lore
- Get world summaries and location contents

## Quick Start

### Prerequisites
- Docker and Docker Compose
- (Optional) Python 3.12+ for local development

### Run with Docker

```bash
# Start the server and MongoDB
docker compose up

# The MCP server will be available at http://localhost:8080
```

### Run Tests

```bash
# Run all tests
docker compose run --rm test

# Or run specific tests
docker compose run --rm test pytest tests/test_characters.py -v
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Start MongoDB (using Docker)
docker compose up mongo -d

# Run the server
python -m src.server
```

## MCP Tools

### World Creation (6 tools)
| Tool | Description |
|------|-------------|
| `set_world` | Create, update, or delete a world |
| `set_lore` | Create, update, or delete lore entries |
| `set_location` | Create, update, or delete locations |
| `set_faction` | Create, update, or delete factions |
| `set_item_blueprint` | Create, update, or delete item templates |
| `set_ability_blueprint` | Create, update, or delete ability templates |

### Characters (14 tools)
| Tool | Description |
|------|-------------|
| `create_character` | Create a new PC or NPC |
| `delete_character` | Remove a character |
| `rename_character` | Update name/description |
| `move_character` | Change location |
| `set_level` | Set character level |
| `set_attribute` | Set an attribute (HP, MP, etc.) |
| `set_skill` | Set a skill value |
| `grant_ability` | Give an ability |
| `revoke_ability` | Remove an ability |
| `apply_status` | Apply a status effect |
| `remove_status` | Remove a status effect |
| `join_faction` | Join a faction |
| `leave_faction` | Leave a faction |
| `set_faction_standing` | Update faction rank/reputation |

### Items (8 tools)
| Tool | Description |
|------|-------------|
| `spawn_item` | Create an item (from template or custom) |
| `destroy_item` | Remove an item |
| `give_item` | Transfer to a character |
| `drop_item` | Place at a location |
| `set_item_quantity` | Change stack count |
| `set_item_attribute` | Modify an attribute |
| `apply_item_status` | Add a condition |
| `remove_item_status` | Remove a condition |

### Quests & Story (8 tools)
| Tool | Description |
|------|-------------|
| `create_quest` | Create a new quest |
| `delete_quest` | Remove a quest |
| `begin_quest` | Assign to a character |
| `update_quest` | Update progress/objectives |
| `complete_quest` | Mark quest finished |
| `record_event` | Log a game event |
| `delete_event` | Remove an event |
| `set_chronicle` | Create/update story summaries |

### Groups (6 tools)
| Tool | Description |
|------|-------------|
| `form_party` | Create a party |
| `disband_party` | Dissolve a party |
| `rename_party` | Update name/description |
| `add_to_party` | Add a member |
| `remove_from_party` | Remove a member |
| `set_party_leader` | Set the leader |

### Time (3 tools)
| Tool | Description |
|------|-------------|
| `get_game_time` | Get current game time |
| `set_game_time` | Set game time |
| `advance_game_time` | Move time forward |

### Queries (12 tools)
| Tool | Description |
|------|-------------|
| `get_entity` | Fetch any entity by ID |
| `find_characters` | Search characters |
| `find_items` | Search items |
| `find_locations` | Search locations |
| `find_nearby_locations` | Geo search |
| `find_quests` | Search quests |
| `find_events` | Search timeline |
| `search_lore` | Full-text search lore |
| `find_factions` | Search factions |
| `find_parties` | Search parties |
| `get_world_summary` | World overview |
| `get_location_contents` | Characters/items at location |

## Data Model

The server uses a flexible, game-system-agnostic data model:

- **World**: Game container with custom settings
- **Character**: PCs and NPCs with flexible attributes, skills, abilities
- **ItemTemplate/Item**: Blueprints and instances
- **AbilityTemplate**: Ability definitions
- **Location**: Places with hierarchy and geo-coordinates
- **Faction**: Organizations with relationships
- **Party**: Informal character groups
- **Quest**: Objectives with progress tracking
- **Event**: Detailed game state changes
- **Chronicle**: Summarized story beats
- **Lore**: World history and background

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | `rpg_mcp` | Database name |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8080` | Server port |

## License

MIT
