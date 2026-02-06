"""Configuration management for RPG MCP server."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    db_name: str = "rpg_mcp"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8080
    
    # Auth (stubbed for now)
    auth_enabled: bool = False
    auth_service_url: str = ""


settings = Settings()
