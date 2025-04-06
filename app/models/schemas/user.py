from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    name: Optional[str] = None
    image: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    pass


class GoogleTokenVerify(BaseModel):
    """Schema for Google token verification"""
    id_token: str


class UserUpdate(BaseModel):
    """User update schema with optional fields"""
    name: Optional[str] = None
    image: Optional[str] = None


class UserInDB(UserBase):
    """User schema as stored in the database"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_login: datetime = Field(default_factory=datetime.utcnow)
    xp_points: int = 0
    level: int = 1
    games_played: int = 0
    
    @validator('id', pre=True)
    def ensure_id_is_string(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v


class UserResponse(UserBase):
    """User response schema for API responses"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: datetime
    xp_points: int
    level: int
    games_played: int

    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """User statistics schema"""
    id: str
    xp_points: int
    level: int
    games_played: int
    
    class Config:
        from_attributes = True


class UpdateXPRequest(BaseModel):
    """Request schema for updating XP points"""
    xp_increase: int = Field(..., gt=0)


class TokenPayload(BaseModel):
    """Token payload schema"""
    sub: str
    exp: int
    jti: str
    type: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"