from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class GameType(BaseModel):
    """Game type schema"""
    id: str
    name: str
    description: str


class QuizQuestion(BaseModel):
    """Quiz question schema"""
    question: str
    answers: List[str]
    correct_answer: str
    difficulty: str


class GameContentRequest(BaseModel):
    """Request for generating game content"""
    content: str = Field(..., min_length=10)
    game: str = Field(..., min_length=2)


class GameContentResponse(BaseModel):
    """Response with generated game content"""
    questions: List[QuizQuestion]
    game_type: str


class GameSession(BaseModel):
    """Game session schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    game_type: str
    content_source: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    score: Optional[int] = None
    xp_earned: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('id', pre=True)
    def ensure_id_is_string(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v


class GameSessionCreate(BaseModel):
    """Game session creation schema"""
    game_type: str
    content_source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GameSessionUpdate(BaseModel):
    """Game session update schema"""
    completed_at: Optional[datetime] = None
    score: Optional[int] = None
    xp_earned: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class GameSessionResponse(GameSession):
    """Game session response schema"""
    class Config:
        from_attributes = True


class GameStatistics(BaseModel):
    """Game statistics schema"""
    user_id: str
    game_type: str
    sessions_played: int
    total_score: int
    average_score: float
    total_xp_earned: int
    best_score: int
    last_played: Optional[datetime] = None

    class Config:
        from_attributes = True