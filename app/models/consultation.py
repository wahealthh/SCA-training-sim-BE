from sqlalchemy import String, Text, Float, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime
from sqlalchemy.sql import func

from app.models.base_model import BaseModel, Base


class Consultation(BaseModel, Base):
    """
    Consultation record including transcript, scoring, and audio recording
    """
    __tablename__ = "consultations"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    patient_case_id: Mapped[int] = mapped_column(ForeignKey("patient_cases.id"), nullable=False)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)  
    
    # Store domain scores as JSON
    domain_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Audio recording URL or data
    audio_recording: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="consultations")
    patient_case = relationship("PatientCase", back_populates="consultations")
    peer_comments = relationship("PeerComment", back_populates="consultation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Consultation(id={self.id}, overall_score={self.overall_score})>"


class PatientCase(BaseModel, Base):
    """
    Patient case model for consultation scenarios
    """
    __tablename__ = "patient_cases"
    
    age: Mapped[int] = mapped_column(nullable=False)
    presenting: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Relationships
    consultations = relationship("Consultation", back_populates="patient_case")
    
    def __repr__(self):
        return f"<PatientCase(id={self.id}, presenting='{self.presenting[:30]}...')>"


class PeerComment(BaseModel, Base):
    """
    Comments from peers on shared consultations
    """
    __tablename__ = "peer_comments"
    
    consultation_id: Mapped[int] = mapped_column(ForeignKey("consultations.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment: Mapped[str] = mapped_column(String(300), nullable=False)
    
    # Relationships
    consultation = relationship("Consultation", back_populates="peer_comments")
    user = relationship("User", back_populates="comments")
    
    def __repr__(self):
        return f"<PeerComment(id={self.id}, user_id={self.user_id})>"