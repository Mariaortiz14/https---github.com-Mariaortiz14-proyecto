from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    name: str
    surname: Optional[str] = None
    age: int
    phone: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        orm_mode = True

class EventCreate(BaseModel):
    name: str
    description: str
    date: datetime
    location: str

class EventResponse(BaseModel):
    id: int
    name: str
    description: str
    date: datetime
    location: str

    class Config:
        orm_mode = True
