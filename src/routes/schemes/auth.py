from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class User(UserBase):
    user_id: int
    user_uuid: str
    is_active: bool
    is_superuser: bool
    
    @field_validator('user_uuid', mode='before')
    @classmethod
    def convert_uuid_to_string(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None 