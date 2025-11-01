"""SQLAlchemy database models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SearchLog(Base):
    """Search logs for analytics"""
    
    __tablename__ = "search_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(255), index=True, nullable=True)
    request_json = Column(JSON, nullable=False)
    response_meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SavedSearch(Base):
    """Saved searches"""
    
    __tablename__ = "saved_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True, nullable=False)
    request_json = Column(JSON, nullable=False)
    results_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Feedback(Base):
    """User feedback on places"""
    
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String(255), index=True, nullable=False)
    user_id = Column(String(255), index=True, nullable=False)
    thumbs_up = Column(Boolean, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Profile(Base):
    """User profiles for personalization"""
    
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to preferences
    preferences = relationship("ProfilePreference", back_populates="profile", cascade="all, delete-orphan")


class ProfilePreference(Base):
    """User preferences"""
    
    __tablename__ = "profile_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    key = Column(String(255), nullable=False)
    value = Column(String(255), nullable=False)
    weight = Column(Float, default=0.5, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship to profile
    profile = relationship("Profile", back_populates="preferences")