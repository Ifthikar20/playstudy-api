from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid


@dataclass
class User:
    """User domain model"""
    id: str
    email: str
    name: Optional[str] = None
    image: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_login: datetime = field(default_factory=datetime.utcnow)
    xp_points: int = 0
    level: int = 1
    games_played: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, email: str, name: Optional[str] = None, image: Optional[str] = None) -> 'User':
        """Create a new user"""
        return cls(
            id=str(uuid.uuid4()),
            email=email,
            name=name,
            image=image,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
        )

    def update_login(self) -> None:
        """Update last login time"""
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_profile(self, name: Optional[str] = None, image: Optional[str] = None) -> None:
        """Update user profile"""
        if name is not None:
            self.name = name
        if image is not None:
            self.image = image
        self.updated_at = datetime.utcnow()

    def add_xp(self, xp_increase: int) -> None:
        """Add XP points and update level"""
        self.xp_points += xp_increase
        self.level = min(max(1, int(self.xp_points / 100) + 1), 100)
        self.updated_at = datetime.utcnow()

    def increment_games_played(self) -> None:
        """Increment games played counter"""
        self.games_played += 1
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for storage"""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "image": self.image,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat(),
            "xp_points": self.xp_points,
            "level": self.level,
            "games_played": self.games_played,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user from dictionary"""
        return cls(
            id=data["id"],
            email=data["email"],
            name=data.get("name"),
            image=data.get("image"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") and isinstance(data["updated_at"], str) else data.get("updated_at"),
            last_login=datetime.fromisoformat(data["last_login"]) if isinstance(data["last_login"], str) else data["last_login"],
            xp_points=data.get("xp_points", 0),
            level=data.get("level", 1),
            games_played=data.get("games_played", 0),
            metadata=data.get("metadata", {}),
        )