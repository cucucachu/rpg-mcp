"""Token validation (stubbed for now).

In production, this will validate tokens against an external auth service
and return the allowed world IDs for the authenticated user.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthContext:
    """Authentication context for a session."""
    token: str
    user_id: Optional[str] = None
    allowed_worlds: list[str] = None
    
    def __post_init__(self):
        if self.allowed_worlds is None:
            self.allowed_worlds = []
    
    def can_access_world(self, world_id: str) -> bool:
        """Check if this session can access a world."""
        # Stubbed: allow all access
        return True


async def validate_token(token: str) -> Optional[AuthContext]:
    """Validate a token and return the auth context.
    
    Stubbed implementation - accepts all tokens.
    
    In production, this would:
    1. Call external auth service to validate token
    2. Get user ID and allowed world IDs
    3. Return AuthContext or None if invalid
    """
    # Stubbed: accept all tokens
    return AuthContext(
        token=token,
        user_id="stub_user",
        allowed_worlds=["*"],  # Allow all worlds
    )
