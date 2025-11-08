from pydantic import BaseModel
from datetime import datetime, date
from models import EventType # Import our new Enum

# --- Schemas for Face Recognition User ---

class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    pass

class User(UserBase): # <-- This was the typo, fixed to UserBase
    id: int
    class Config:
        from_attributes = True 

# --- Schemas for Authentication (Login) ---

class AdminCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

# --- Schemas for Attendance & Reports (V2.0) ---

class AttendanceEvent(BaseModel):
    """
    The new schema for an In/Out event.
    """
    id: int
    user_id: int
    timestamp: datetime
    event_type: EventType
    user: User # Nested user info

    class Config:
        from_attributes = True

class ReportEntry(BaseModel):
    """
    A single entry for the full report.
    """
    name: str
    timestamp: datetime
    status: EventType

    class Config:
        from_attributes = True

class TodayAttendance(BaseModel):
    """
    A simple entry for the "Today" list.
    """
    name: str
    time: str
    status: EventType

    class Config:
        from_attributes = True
        
class TotalHoursEntry(BaseModel):
    """
    An entry for the "Total Hours" report.
    """
    name: str
    total_hours: float
    status: EventType # The last status (IN or OUT)
    
    class Config:
        from_attributes = True