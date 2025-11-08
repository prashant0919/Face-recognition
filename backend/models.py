from sqlalchemy import Column, Integer, String, BLOB, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from database import Base
import datetime
import enum

# This enum defines the two types of clock events
class EventType(str, enum.Enum):
    CLOCK_IN = "IN"
    CLOCK_OUT = "OUT"

class Admin(Base):
    """
    Database model for an Admin user (for login).
    """
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class User(Base):
    """
    Database model for a User (for face recognition).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    encoding = Column(BLOB, nullable=False)

    # A user can have many attendance records
    attendance_records = relationship("Attendance", back_populates="user")

class Attendance(Base):
    """
    Database model for an Attendance record.
    REWRITTEN for In/Out logic.
    """
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # We now store the full timestamp for better calculations
    timestamp = Column(DateTime, default=datetime.datetime.now, nullable=False)
    
    # This column stores "IN" or "OUT"
    event_type = Column(Enum(EventType), nullable=False)

    # Define the relationship back to the User
    user = relationship("User", back_populates="attendance_records")

    # We NO LONGER need a unique constraint on (user, date)
    # A user can have multiple "IN" and "OUT" events per day.