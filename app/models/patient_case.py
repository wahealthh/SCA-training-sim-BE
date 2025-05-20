from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base_model import BaseModel, Base


class PatientCase(BaseModel, Base):
    """
    Patient case model for consultation scenarios
    """
    __tablename__ = 'patient_cases'
    
    age = Column(Integer, nullable=False)
    presenting = Column(Text, nullable=False) 
    context = Column(Text, nullable=False)
    
    # Relationships
    consultations = relationship("Consultation", back_populates="patient_case")
    
    def __repr__(self):
        return f"<PatientCase(id={self.id}, presenting='{self.presenting[:30]}...')>" 