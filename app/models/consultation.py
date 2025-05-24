from sqlalchemy import Column, Integer, Text, Float, Boolean, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base_model import BaseModel, Base


class Consultation(BaseModel, Base):
    """
    Consultation record including transcript, scoring, and audio recording
    """
    __tablename__ = 'consultations'
    
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    case_id = Column(String(36), ForeignKey('cases.id'), nullable=False)
    transcript = Column(Text, nullable=False)
    overall_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    is_shared = Column(Boolean, default=False, nullable=False)
    coverage_analysis = Column(JSON, nullable=True)
    domain_scores = Column(JSON, nullable=True)

    
    audio_recording = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    user = relationship("User", back_populates="consultations")
    case = relationship("Case", back_populates="consultations")
    peer_comments = relationship("PeerComment", back_populates="consultation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Consultation(id={self.id}, overall_score={self.overall_score})>"


class PeerComment(BaseModel, Base):
    """
    Comments from peers on shared consultations
    """
    __tablename__ = 'peer_comments'
    
    consultation_id = Column(String(36), ForeignKey('consultations.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    comment = Column(String(300), nullable=False)
    
    consultation = relationship("Consultation", back_populates="peer_comments")
    user = relationship("User")
    
    def __repr__(self):
        return f"<PeerComment(id={self.id}, user_id={self.user_id})>" 